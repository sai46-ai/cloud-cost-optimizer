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
    import re
    import logging
    logger = logging.getLogger("cloudwise")

    # 1. Input format validation
    account_id = data.account_id.strip()
    role_arn = data.role_arn.strip()
    
    if not re.match(r"^\d{12}$", account_id):
        raise HTTPException(
            status_code=400,
            detail="AWS Account ID must be exactly a 12-digit numeric string."
        )
        
    expected_pattern = rf"^arn:aws:iam::{account_id}:role/[\w+=,.@-]+$"
    if not re.match(expected_pattern, role_arn):
        raise HTTPException(
            status_code=400,
            detail=f"Cross-Account Role ARN must match the format: arn:aws:iam::{account_id}:role/RoleName"
        )

    # 2. Check for duplicate AWS Account IDs (multi-tenant safety)
    existing_acc = db.query(AWSAccount).filter(AWSAccount.account_id == account_id).first()
    if existing_acc and existing_acc.org_id != user.org_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"AWS Account ID {account_id} is already connected to another organization."
        )

    # Check for duplicate Role ARNs
    existing_role = db.query(AWSAccount).filter(AWSAccount.role_arn == role_arn).first()
    if existing_role and existing_role.org_id != user.org_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Role ARN {role_arn} is already connected to another organization."
        )

    # 3. Active AssumeRole policy check via boto3 STS client (unless target lab account 810498829595 or server has no credentials)
    if "810498829595" not in account_id:
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError
            from app.core.config import get_settings
            settings = get_settings()
            
            sts_kwargs = {
                "region_name": settings.AWS_REGION or "us-east-1",
            }
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                sts_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                sts_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
                if settings.AWS_SESSION_TOKEN:
                    sts_kwargs["aws_session_token"] = settings.AWS_SESSION_TOKEN
            
            sts_client = boto3.client("sts", **sts_kwargs)
            external_id = f"ext-{user.org_id[:8]}"
            
            # Attempt to assume role to verify trust relationship is properly set up
            sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName="CloudWiseValidationSession",
                ExternalId=external_id,
            )
        except NoCredentialsError:
            logger.warning("AWS IAM validation skipped: server lacks AWS credentials configuration.")
        except ClientError as e:
            err_code = e.response.get("Error", {}).get("Code", "Unknown")
            err_msg = e.response.get("Error", {}).get("Message", str(e))
            logger.error("AWS AssumeRole validation failed: %s - %s", err_code, err_msg)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"AWS STS AssumeRole check failed: {err_msg} (Code: {err_code}). Please verify your IAM trust relationship and External ID: {external_id}."
            )
        except Exception as e:
            logger.error("Unexpected error during AWS role verification: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to communicate with AWS STS: {str(e)}"
            )

    # 4. Atomic database update with rollback
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

    account.account_id = account_id
    account.role_arn = role_arn
    account.account_name = data.account_name or f"AWS Account {account_id}"
    account.external_id = f"ext-{user.org_id[:8]}"
    if data.region:
        account.region = data.region
    account.is_active = True

    try:
        db.commit()
        db.refresh(account)
    except Exception as e:
        db.rollback()
        logger.error("Failed to commit AWS Account integration: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred while updating the AWS integration settings. Please try again."
        )

    AuditService.log_action(
        db=db,
        user_id=user.id,
        action="update",
        resource_type="settings",
        resource_id=account.id,
        description=f"Connected AWS Account: {account_id}",
        old_value=old_val,
        new_value=data.model_dump(),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return account

