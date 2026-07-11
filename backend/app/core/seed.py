"""
Development Administrator Seeding logic.
Creates the default admin account only if it does not exist.
"""
import logging
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.models.organization import Organization
from app.core.security import hash_password

logger = logging.getLogger("cloudwise")

def seed_development_admin(db: Session) -> None:
    """Create the development admin account if it does not already exist."""
    admin_email = "admin@gmail.com"
    
    # Check if admin already exists
    existing = db.query(User).filter(User.email == admin_email).first()
    if existing:
        logger.info("Development admin account already exists. Skipping seed.")
        return

    logger.info("Seeding development admin account: %s", admin_email)
    
    try:
        # Ensure a default organization exists for the admin
        org_slug = "admin-organization"
        org = db.query(Organization).filter(Organization.slug == org_slug).first()
        if not org:
            org = Organization(
                name="Admin Organization",
                slug=org_slug,
                plan="enterprise",
                is_active=True
            )
            db.add(org)
            db.commit()
            db.refresh(org)
            logger.info("Created Admin Organization.")
            
        # Create default administrator
        admin_user = User(
            email=admin_email,
            full_name="System Administrator",
            hashed_password=hash_password("123456789"),
            role=UserRole.ADMIN.value,
            org_id=org.id,
            is_active=True,
            account_status="active"
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        logger.info("Successfully seeded development admin account.")
    except Exception as e:
        db.rollback()
        logger.error("Failed to seed development admin account: %s", e)
