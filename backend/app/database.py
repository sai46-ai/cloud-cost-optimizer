from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from sqlalchemy.exc import OperationalError
from typing import Generator
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

from typing import Dict, Any

connect_args: Dict[str, Any] = {}
engine_kwargs: Dict[str, Any] = {
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
    """Create all database tables and run programmatic migrations."""
    import app.models  # Ensure models are registered on Base metadata
    Base.metadata.create_all(bind=engine)

    # Programmatic schema migration for SQLite/Postgres to preserve existing users
    from sqlalchemy import inspect, text
    try:
        inspector = inspect(engine)
        if "users" in inspector.get_table_names():
            columns = [col["name"] for col in inspector.get_columns("users")]
            with engine.begin() as conn:
                if "account_status" not in columns:
                    logger.info("Database migration: adding column 'account_status' to users table")
                    # SQLite supports ALTER TABLE ADD COLUMN
                    conn.execute(text("ALTER TABLE users ADD COLUMN account_status VARCHAR(20) DEFAULT 'active'"))
                if "last_login" not in columns:
                    logger.info("Database migration: adding column 'last_login' to users table")
                    conn.execute(text("ALTER TABLE users ADD COLUMN last_login TIMESTAMP"))
                
                # Assign USER as the default role for existing accounts
                logger.info("Database migration: migrating legacy user roles to uppercase")
                conn.execute(text("UPDATE users SET role = 'USER' WHERE role IN ('viewer', 'manager', 'user', 'viewers') OR role IS NULL"))
                conn.execute(text("UPDATE users SET role = 'ADMIN' WHERE role IN ('admin', 'admins')"))
    except Exception as e:
        logger.warning("Programmatic database schema upgrade warning: %s", e)
