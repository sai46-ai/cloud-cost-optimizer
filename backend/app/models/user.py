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

    # Isolated Demo and AWS Relationships
    demo_user = relationship("DemoUser", back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="selectin")
    demo_cost_records = relationship("DemoCostRecord", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    aws_cost_records = relationship("AWSCostRecord", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    demo_budgets = relationship("DemoBudget", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    aws_budgets = relationship("AWSBudget", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    demo_recommendations = relationship("DemoRecommendation", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    aws_recommendations = relationship("AWSRecommendation", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    demo_forecasts = relationship("DemoForecast", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    aws_forecasts = relationship("AWSForecast", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    demo_reports = relationship("DemoReport", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    aws_reports = relationship("AWSReport", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    demo_alerts = relationship("DemoAlert", back_populates="user", cascade="all, delete-orphan", lazy="selectin")
    aws_alerts = relationship("AWSAlert", back_populates="user", cascade="all, delete-orphan", lazy="selectin")

    @property
    def is_demo_mode(self) -> bool:
        # If they connected a real, active AWS account (not a seeded demo one), they are NOT in demo mode
        if self.organization:
            real_accounts = [acc for acc in self.organization.aws_accounts if acc.is_active and not getattr(acc, "is_demo", False)]
            if real_accounts:
                return False
        # Otherwise, they are in demo mode!
        return True

    @property
    def is_aws_connected(self) -> bool:
        if not self.organization:
            return False
        # Returns True only if they have connected a real, active AWS account
        return any(acc.is_active and not getattr(acc, "is_demo", False) for acc in self.organization.aws_accounts)

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class DemoUser(Base):
    __tablename__ = "demo_users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="USER")
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    user = relationship("User", back_populates="demo_user")

    def __repr__(self) -> str:
        return f"<DemoUser {self.email}>"
