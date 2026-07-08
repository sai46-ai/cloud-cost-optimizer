"""
CloudWise AI - Security Module
JWT token management, password hashing, and authentication utilities.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
import bcrypt

from app.core.config import get_settings

settings = get_settings()


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    passwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(passwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        passwd_bytes = plain_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(passwd_bytes, hashed_bytes)
    except Exception:
        return False


def create_access_token(
    user_id: str, role: str, extra_claims: Optional[dict] = None
) -> str:
    """Create a short-lived JWT access token."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Create a long-lived JWT refresh token."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token. Raises jwt.PyJWTError on failure."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


class TokenPayload:
    """Parsed JWT token payload."""

    def __init__(self, payload: dict):
        self.user_id: str = payload.get("sub", "")
        self.role: str = payload.get("role", "viewer")
        self.token_type: str = payload.get("type", "access")
        self.exp: datetime = datetime.fromtimestamp(
            payload.get("exp", 0), tz=timezone.utc
        )

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.exp
