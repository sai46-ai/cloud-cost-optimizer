"""
API Dependencies
Shared FastAPI dependencies for auth, database, and RBAC.
"""

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.auth_service import AuthService
from app.core.exceptions import unauthorized, forbidden
from app.models.user import User

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate the current user from JWT token."""
    if not credentials:
        raise unauthorized()
    try:
        auth_service = AuthService(db)
        return auth_service.get_current_user(credentials.credentials)
    except Exception:
        raise unauthorized("Invalid or expired token")


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Optionally extract user — returns None if no token provided."""
    if not credentials:
        return None
    try:
        auth_service = AuthService(db)
        return auth_service.get_current_user(credentials.credentials)
    except Exception:
        return None


def require_role(*roles: str):
    """Factory for role-based access control dependency."""

    async def role_checker(user: User = Depends(get_current_user)):
        if user.role not in roles:
            raise forbidden(
                f"Role '{user.role}' is not authorized. Required: {', '.join(roles)}"
            )
        return user

    return role_checker


# Role shortcuts
require_admin = require_role("ADMIN")
require_reviewer = require_role("ADMIN", "REVIEWER")
require_user = require_role("ADMIN", "USER")
require_any = require_role("ADMIN", "REVIEWER", "USER")

# Legacy compatibility shortcuts mapped to any authenticated role
require_manager = require_any
require_viewer = require_any
