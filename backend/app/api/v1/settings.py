from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.settings import UserSettings
from app.services.audit_service import AuditService
from app.schemas.settings import (
    SettingsResponse,
    SettingsUpdate,
    AWSAccountResponse,
    AWSAccountUpdate,
)
from app.models.aws_account import AWSAccount

router = APIRouter()


@router.get("/", response_model=SettingsResponse)
def get_settings(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user's settings."""
    settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    if not settings:
        settings = UserSettings(user_id=user.id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.put("/", response_model=SettingsResponse)
def update_settings(
    request: Request,
    data: SettingsUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user settings."""
    settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    old_val = None
    if settings:
        old_val = {
            "theme": settings.theme,
            "currency": settings.currency,
            "email_notifications": settings.email_notifications,
            "slack_notifications": settings.slack_notifications,
            "weekly_reports": settings.weekly_reports,
            "anomaly_alerts": settings.anomaly_alerts,
        }
    else:
        settings = UserSettings(user_id=user.id)
        db.add(settings)

    for key, value in data.model_dump().items():
        setattr(settings, key, value)

    db.commit()
    db.refresh(settings)

    AuditService.log_action(
        db=db,
        user_id=user.id,
        action="update",
        resource_type="settings",
        resource_id=settings.id,
        description="Updated system settings",
        old_value=old_val,
        new_value=data.model_dump(),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return settings


@router.get("/aws", response_model=AWSAccountResponse)
def get_aws_account(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get connected AWS Account details for user's organization."""
    account = db.query(AWSAccount).filter(AWSAccount.org_id == user.org_id).first()
    if not account:
        # Return empty response — user must configure their own AWS account
        return AWSAccountResponse(
            id="",
            org_id=user.org_id or "",
            account_id="",
            account_name="",
            role_arn="",
            external_id=None,
            region="",
            is_active=False,
        )
    return account


@router.put("/aws", response_model=AWSAccountResponse)
def update_aws_account(
    request: Request,
    data: AWSAccountUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update organization AWS integration settings."""
    account = db.query(AWSAccount).filter(AWSAccount.org_id == user.org_id).first()
    old_val = None
    if account:
        old_val = {
            "account_id": account.account_id,
            "role_arn": account.role_arn,
            "account_name": account.account_name,
            "region": account.region,
        }
    else:
        account = AWSAccount(org_id=user.org_id)
        db.add(account)

    account.account_id = data.account_id
    account.role_arn = data.role_arn
    account.account_name = data.account_name or f"AWS Account {data.account_id}"
    if data.region:
        account.region = data.region

    db.commit()
    db.refresh(account)

    AuditService.log_action(
        db=db,
        user_id=user.id,
        action="update",
        resource_type="settings",
        resource_id=account.id,
        description=f"Connected AWS Account: {data.account_id}",
        old_value=old_val,
        new_value=data.model_dump(),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return account

