"""
Authentication Service
Handles user registration, login, token management, and password operations.
"""

import logging
from sqlalchemy.orm import Session



from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    TokenPayload,
)
from app.core.config import get_settings
from app.core.exceptions import (
    AuthenticationError,
    DuplicateEntityError,
    EntityNotFoundError,
)
from app.models.user import User
from app.models.organization import Organization
from app.repositories.user_repository import UserRepository
from app.repositories.base import BaseRepository

settings = get_settings()
logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.org_repo = BaseRepository(Organization, db)

    def register(
        self, email: str, password: str, full_name: str, organization_name: str
    ) -> dict:
        """Register a new user and organization."""
        # Check for existing user
        existing = self.user_repo.get_by_email(email)
        if existing:
            raise DuplicateEntityError("User", "email", email)

        # Create organization
        slug = organization_name.lower().replace(" ", "-")
        existing_org = (
            self.db.query(Organization).filter(Organization.slug == slug).first()
        )
        if existing_org:
            raise DuplicateEntityError("Organization", "name", organization_name)

        org = Organization(name=organization_name, slug=slug)
        self.org_repo.create(org)

        # Create user (first user is ADMIN)
        is_first = self.user_repo.count() == 0
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=hash_password(password),
            org_id=org.id,
            role="ADMIN" if is_first else "USER",
        )
        self.user_repo.create(user)

        # Auto-seed financial records for new registration ONLY if user is a reviewer
        if user.is_demo_mode:
            try:
                from seed import seed_user_data
                seed_user_data(user, self.db)
            except Exception as e:
                logger.warning("Failed to auto-seed user data: %s", e)

        return self._generate_tokens(user)

    def login(self, email: str, password: str) -> dict:
        """Authenticate a user and return tokens."""
        user = self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")
        if not user.is_active or user.account_status == "disabled":
            raise AuthenticationError("Account is disabled")
        
        # Update last login timestamp
        from datetime import datetime, timezone
        user.last_login = datetime.now(timezone.utc)
        self.db.commit()
        
        # If user is reviewer, ensure demo data is seeded
        if user.is_demo_mode:
            from app.models.cost_record import CostRecord
            exists = self.db.query(CostRecord).filter_by(user_id=user.id).first()
            if not exists:
                try:
                    from seed import seed_user_data
                    seed_user_data(user, self.db)
                except Exception as e:
                    logger.warning("Failed to auto-seed reviewer user data on login: %s", e)
                    
        return self._generate_tokens(user)

    def refresh_token(self, refresh_token: str) -> dict:
        """Generate new access token from a valid refresh token."""
        try:
            payload = decode_token(refresh_token)
            tp = TokenPayload(payload)
            if tp.token_type != "refresh":
                raise AuthenticationError("Invalid token type")
        except Exception:
            raise AuthenticationError("Invalid or expired refresh token")

        user = self.user_repo.get_by_id(tp.user_id)
        if not user or not user.is_active or user.account_status == "disabled":
            raise AuthenticationError("User not found or disabled")

        return self._generate_tokens(user)

    def get_current_user(self, token: str) -> User:
        """Validate access token and return the user."""
        try:
            payload = decode_token(token)
            tp = TokenPayload(payload)
            if tp.token_type != "access":
                raise AuthenticationError("Invalid token type")
        except Exception:
            raise AuthenticationError("Invalid or expired token")

        user = self.user_repo.get_by_id(tp.user_id)
        if not user or not user.is_active or user.account_status == "disabled":
            raise AuthenticationError("User not found or disabled")
        return user

    def change_password(
        self, user_id: str, current_password: str, new_password: str
    ) -> None:
        """Change user password."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError("User", user_id)
        if not verify_password(current_password, user.hashed_password):
            raise AuthenticationError("Current password is incorrect")
        self.user_repo.update(user, {"hashed_password": hash_password(new_password)})

    def update_profile(self, user_id: str, email: str, full_name: str) -> dict:
        """Update user profile."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError("User", user_id)
        if email != user.email:
            existing = self.user_repo.get_by_email(email)
            if existing:
                raise DuplicateEntityError("User", "email", email)
        self.user_repo.update(user, {"email": email, "full_name": full_name})
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "account_status": user.account_status,
            "last_login": user.last_login,
            "avatar_url": user.avatar_url,
            "org_id": user.org_id,
            "created_at": user.created_at,
            "is_demo_mode": user.is_demo_mode,
            "is_aws_connected": user.is_aws_connected,
        }

    def _generate_tokens(self, user: User) -> dict:
        access_token = create_access_token(user.id, user.role)
        refresh = create_refresh_token(user.id)
        return {
            "access_token": access_token,
            "refresh_token": refresh,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
                "account_status": user.account_status,
                "last_login": user.last_login,
                "avatar_url": user.avatar_url,
                "org_id": user.org_id,
                "created_at": user.created_at,
                "is_demo_mode": user.is_demo_mode,
                "is_aws_connected": user.is_aws_connected,
            },
        }
