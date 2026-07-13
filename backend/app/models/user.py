import enum
from sqlalchemy import String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid


class UserRole(str, enum.Enum):
    USER = "USER"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    org_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(50), default="USER", server_default="USER"
    )  # USER
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    account_status: Mapped[str] = mapped_column(
        String(20), default="active", server_default="active"
    )  # active, disabled
    last_login: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    avatar_url: Mapped[str] = mapped_column(String(500), nullable=True)

    # Relationships
    organization = relationship("Organization", back_populates="users", lazy="selectin")
    cost_records = relationship("CostRecord", back_populates="user", lazy="selectin")
    budgets = relationship(
        "Budget", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    recommendations = relationship(
        "Recommendation", back_populates="user", lazy="selectin"
    )
    forecasts = relationship("Forecast", back_populates="user", lazy="selectin")
    reports = relationship("Report", back_populates="user", lazy="selectin")
    audit_logs = relationship("AuditLog", back_populates="user", lazy="selectin")
    settings = relationship(
        "UserSettings",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def is_demo_mode(self) -> bool:
        return True

    @property
    def is_aws_connected(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"<User {self.email}>"
