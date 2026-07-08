"""Settings model for user preferences."""

from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid


class UserSettings(Base, TimestampMixin):
    __tablename__ = "user_settings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), unique=True, nullable=False
    )

    # Security
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    # Notifications
    email_alerts: Mapped[bool] = mapped_column(Boolean, default=True)
    slack_alerts: Mapped[bool] = mapped_column(Boolean, default=False)
    slack_webhook_url: Mapped[str] = mapped_column(String(500), nullable=True)
    weekly_reports: Mapped[bool] = mapped_column(Boolean, default=True)

    # Preferences
    theme: Mapped[str] = mapped_column(String(20), default="dark")
    currency: Mapped[str] = mapped_column(String(10), default="USD")

    # Relationships
    user = relationship("User", back_populates="settings")

    def __repr__(self) -> str:
        return f"<UserSettings user_id={self.user_id}>"
