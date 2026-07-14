"""
Development Administrator Seeding logic.
Creates the default admin account only if it does not exist.
"""
import logging
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.organization import Organization
from app.core.security import hash_password

logger = logging.getLogger("cloudwise")

DEFAULT_ADMIN_EMAIL = "admin@cloudwise.ai"
DEFAULT_ADMIN_PASSWORD = "CloudWise@2024"

def seed_development_admin(db: Session) -> None:
    """Create the development default user account if it does not already exist."""
    admin_email = DEFAULT_ADMIN_EMAIL

    # Check if admin already exists
    existing = db.query(User).filter(User.email == admin_email).first()
    if existing:
        # Ensure the admin account is always active and has correct status
        needs_update = False
        if existing.is_active is not True:
            existing.is_active = True
            needs_update = True
        if existing.account_status != "active":
            existing.account_status = "active"
            needs_update = True
        if needs_update:
            db.commit()
            logger.info("Updated development admin account to ensure it is active.")
        else:
            logger.info("Development default user account already exists. Skipping seed.")
        return

    logger.info("Seeding development default user account: %s", admin_email)

    try:
        # Ensure a default organization exists
        org_slug = "cloudwise-demo-org"
        org = db.query(Organization).filter(Organization.slug == org_slug).first()
        if not org:
            org = Organization(
                name="CloudWise Demo Organization",
                slug=org_slug,
                plan="enterprise",
                is_active=True
            )
            db.add(org)
            db.commit()
            db.refresh(org)
            logger.info("Created CloudWise Demo Organization.")

        # Create default user
        admin_user = User(
            email=admin_email,
            full_name="CloudWise Admin",
            hashed_password=hash_password(DEFAULT_ADMIN_PASSWORD),
            role="USER",
            org_id=org.id,
            is_active=True,
            account_status="active"
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        logger.info("Successfully seeded development default user account: %s / %s", admin_email, DEFAULT_ADMIN_PASSWORD)
    except Exception as e:
        db.rollback()
        logger.error("Failed to seed development admin account: %s", e)
