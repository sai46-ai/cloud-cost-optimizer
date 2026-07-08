from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from sqlalchemy.exc import OperationalError
from typing import Generator
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

connect_args = {}
engine_kwargs = {
    "pool_pre_ping": True,
    "echo": settings.DEBUG,
}

is_sqlite_db = settings.is_sqlite
fallback_sqlite_url = "sqlite:///./cloudwise.db"

if is_sqlite_db:
    connect_args = {"check_same_thread": False}
    engine = create_engine(
        settings.DATABASE_URL, connect_args=connect_args, **engine_kwargs
    )
else:
    engine_kwargs["pool_size"] = 5
    engine_kwargs["max_overflow"] = 10
    try:
        # Create a temp engine and try to connect
        temp_engine = create_engine(settings.DATABASE_URL, **engine_kwargs)
        with temp_engine.connect() as conn:
            pass
        engine = temp_engine
        logger.info("Connected to PostgreSQL successfully.")
    except (OperationalError, Exception) as e:
        logger.warning(
            "PostgreSQL connection failed. Falling back to SQLite. Error: %s", e
        )
        is_sqlite_db = True
        connect_args = {"check_same_thread": False}
        engine_kwargs = {
            "pool_pre_ping": True,
            "echo": settings.DEBUG,
        }
        engine = create_engine(
            fallback_sqlite_url, connect_args=connect_args, **engine_kwargs
        )

# Enable WAL mode for SQLite for better concurrent performance
if is_sqlite_db:

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions with proper cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all database tables. Used for development / initial setup."""
    Base.metadata.create_all(bind=engine)
