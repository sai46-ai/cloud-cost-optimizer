"""Authentication and user schemas."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# --- Auth ---
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=255)
    organization_name: str = Field(min_length=2, max_length=255)
    role: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthResponse(TokenResponse):
    user: "UserResponse"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# --- User ---
class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    account_status: str
    last_login: Optional[datetime] = None
    avatar_url: Optional[str] = None
    org_id: str
    created_at: datetime
    is_demo_mode: bool
    is_aws_connected: bool

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)
