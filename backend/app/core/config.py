"""
CloudWise AI - Core Configuration
Pydantic Settings for environment-based configuration management.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    APP_NAME: str = "CloudWise AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./cloudwise.db",
        description="PostgreSQL or SQLite connection string",
    )

    # Security
    SECRET_KEY: str = Field(
        default="cloudwise-dev-secret-key-change-in-production",
        description="JWT signing secret",
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12

    # AWS
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_SESSION_TOKEN: Optional[str] = None
    AWS_REGION: str = "us-east-1"

    # Redis / Celery
    REDIS_URL: str = "redis://127.0.0.1:6379"
    CELERY_BROKER_URL: str = "redis://127.0.0.1:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://127.0.0.1:6379/0"

    # Gemini AI
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3.5-flash"


    # S3
    S3_BUCKET_REPORTS: str = "cloudwise-reports"

    # Email / SES
    SES_SENDER_EMAIL: str = "noreply@cloudwise.ai"

    # CORS
    CORS_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"
    )

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100

    # Whitelist of Reviewer accounts for Demo Mode (comma-separated)
    REVIEWER_EMAILS: str = "reviewer1@example.com,reviewer2@example.com,qa@example.com,faculty@example.com"

    # Seeding development admin account (disabled in production or if set to False)
    SEED_DEV_ADMIN: bool = True

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def reviewer_emails_list(self) -> list[str]:
        return [email.strip().lower() for email in self.REVIEWER_EMAILS.split(",") if email.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")


    model_config = {
        "env_file": str(Path(__file__).resolve().parent.parent.parent / ".env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
