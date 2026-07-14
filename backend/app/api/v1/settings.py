from fastapi import APIRouter, Depends, Request, HTTPException, status
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

    db.add(settings)
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

    # 3. Validate the AssumeRole trust relationship via boto3 STS
    from app.core.config import get_settings as _get_settings
    _settings = _get_settings()

    # Use user-provided credentials if supplied in the form, else fall back to server credentials
    _access_key = getattr(data, 'aws_access_key_id', None) or _settings.AWS_ACCESS_KEY_ID
    _secret_key = getattr(data, 'aws_secret_access_key', None) or _settings.AWS_SECRET_ACCESS_KEY
    _session_token = getattr(data, 'aws_session_token', None) or _settings.AWS_SESSION_TOKEN
    _has_creds = bool(_access_key and _secret_key)

    if _has_creds:
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError

            sts_kwargs = {"region_name": _settings.AWS_REGION or "us-east-1"}
            sts_kwargs["aws_access_key_id"] = _access_key
            sts_kwargs["aws_secret_access_key"] = _secret_key
            if _session_token:
                sts_kwargs["aws_session_token"] = _session_token

            sts_client = boto3.client("sts", **sts_kwargs)
            external_id = f"ext-{user.org_id[:8]}"

            sts_client.assume_role(
                RoleArn=role_arn,
                RoleSessionName="CloudWiseValidationSession",
                ExternalId=external_id,
            )
            logger.info("AWS STS AssumeRole validation succeeded for account %s", account_id)

        except NoCredentialsError:
            # No usable credentials — skip validation, save and try later
            logger.warning("AWS STS validation skipped: no valid credentials available.")

        except ClientError as e:
            err_code = e.response.get("Error", {}).get("Code", "Unknown")
            err_msg = e.response.get("Error", {}).get("Message", str(e))
            logger.error("AWS AssumeRole validation failed: %s - %s", err_code, err_msg)

            if err_code == "SignatureDoesNotMatch":
                # Server's own credentials are expired/invalid — skip pre-validation and save anyway.
                # Live data fetch will validate credentials at runtime.
                logger.warning(
                    "Server AWS credentials are invalid/expired (SignatureDoesNotMatch). "
                    "Skipping pre-validation. Account saved; live data fetch will validate."
                )
            elif err_code in ("AccessDenied", "InvalidClientTokenId"):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        f"AWS STS AssumeRole failed: {err_msg} (Code: {err_code}). "
                        f"Ensure the role's trust policy allows AssumeRole from this account "
                        f"and includes External ID: ext-{user.org_id[:8]}."
                    )
                )
            else:
                # For other errors (e.g., NoSuchEntity, MalformedInput) — surface clearly
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"AWS STS AssumeRole check failed: {err_msg} (Code: {err_code}). Verify your IAM trust relationship and External ID: ext-{user.org_id[:8]}."
                )

        except Exception as e:
            logger.error("Unexpected error during AWS role verification: %s", str(e))
            # Non-fatal — save the account and try at runtime
            logger.warning("Skipping STS pre-validation due to unexpected error. Account will be saved.")
    else:
        logger.info("AWS STS validation skipped: no AWS credentials configured on server. Account saved; live data fetch will validate.")


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
    account.is_demo = False  # Mark explicitly as a real (non-demo) account
    if data.region:
        account.region = data.region
    account.is_active = True

    db.add(account)

    try:
        db.commit()
        db.refresh(account)
        from app.services.aws_cost_explorer import cost_explorer_service
        cost_explorer_service.clear_cache_for_account(account_id)
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

