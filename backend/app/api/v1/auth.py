"""Auth API routes — login, register, refresh, profile."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    RefreshTokenRequest,
    UserResponse,
    ChangePasswordRequest,
    AuthResponse,
    TokenResponse,
    UserUpdateRequest,
)
from app.api.deps import get_current_user
from app.models.user import User

from app.core.rate_limit import rate_limiter

router = APIRouter()


@router.post(
    "/register", response_model=AuthResponse, dependencies=[Depends(rate_limiter)]
)
def register(request: Request, data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user and organization."""
    service = AuthService(db)
    result = service.register(
        email=data.email,
        password=data.password,
        full_name=data.full_name,
        organization_name=data.organization_name,
        role=data.role,
    )
    user_id = result.get("user", {}).get("id")
    AuditService.log_action(
        db=db,
        user_id=user_id,
        action="register",
        resource_type="user",
        resource_id=user_id,
        description=f"User {data.email} registered organization {data.organization_name}",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return result


@router.post(
    "/login", response_model=AuthResponse, dependencies=[Depends(rate_limiter)]
)
def login(request: Request, data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT tokens."""
    service = AuthService(db)
    result = service.login(email=data.email, password=data.password)
    user_id = result.get("user", {}).get("id")
    role = result.get("user", {}).get("role")
    action = "admin_login" if role == "ADMIN" else "login"
    description = f"Admin logged in: {data.email}" if role == "ADMIN" else f"User logged in: {data.email}"
    
    AuditService.log_action(
        db=db,
        user_id=user_id,
        action=action,
        resource_type="user",
        resource_id=user_id,
        description=description,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return result


@router.post("/refresh", response_model=AuthResponse)
def refresh_token(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh an expired access token."""
    service = AuthService(db)
    return service.refresh_token(data.refresh_token)


@router.get("/me", response_model=UserResponse)
def get_profile(user: User = Depends(get_current_user)):
    """Get current user profile."""
    return user


@router.put("/me", response_model=UserResponse)
def update_profile(
    request: Request,
    data: UserUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current user profile details."""
    service = AuthService(db)
    old_val = {"email": user.email, "full_name": user.full_name}
    result = service.update_profile(user.id, email=data.email, full_name=data.full_name)
    new_val = {"email": data.email, "full_name": data.full_name}
    AuditService.log_action(
        db=db,
        user_id=user.id,
        action="update",
        resource_type="settings",
        resource_id=user.id,
        description="Updated profile settings",
        old_value=old_val,
        new_value=new_val,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return result


@router.post("/change-password")
def change_password(
    request: Request,
    data: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change current user's password."""
    service = AuthService(db)
    service.change_password(user.id, data.current_password, data.new_password)
    AuditService.log_action(
        db=db,
        user_id=user.id,
        action="update",
        resource_type="settings",
        resource_id=user.id,
        description="Changed account password",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return {"message": "Password changed successfully"}

