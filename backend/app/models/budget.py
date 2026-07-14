"""Budget model with tiered alerting thresholds."""

from sqlalchemy import String, Float, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Budget(Base, TimestampMixin):
    __tablename__ = "budgets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    period: Mapped[str] = mapped_column(
        String(20), default="monthly"
    )  # daily, weekly, monthly
    spent: Mapped[float] = mapped_column(Float, default=0.0)
    # Alert thresholds (percentage of budget)
    alert_threshold_50: Mapped[bool] = mapped_column(Boolean, default=True)
    alert_threshold_80: Mapped[bool] = mapped_column(Boolean, default=True)
    alert_threshold_90: Mapped[bool] = mapped_column(Boolean, default=True)
    alert_threshold_100: Mapped[bool] = mapped_column(Boolean, default=True)
    # Notification channels
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    sns_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    dashboard_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="budgets")

    @property
    def utilization_pct(self) -> float:
        if self.amount <= 0:
            return 0.0
        return round((self.spent / self.amount) * 100, 1)

    @property
    def status(self) -> str:
        pct = self.utilization_pct
        if pct >= 100:
            return "exceeded"
        elif pct >= 90:
            return "critical"
        elif pct >= 80:
            return "warning"
        elif pct >= 50:
            return "caution"
        return "healthy"

    def __repr__(self) -> str:
        return f"<Budget {self.name} ${self.amount}>"


class DemoBudget(Base, TimestampMixin):
    __tablename__ = "demo_budgets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    period: Mapped[str] = mapped_column(String(20), default="monthly")  # daily, weekly, monthly
    spent: Mapped[float] = mapped_column(Float, default=0.0)
    alert_threshold_50: Mapped[bool] = mapped_column(Boolean, default=True)
    alert_threshold_80: Mapped[bool] = mapped_column(Boolean, default=True)
    alert_threshold_90: Mapped[bool] = mapped_column(Boolean, default=True)
    alert_threshold_100: Mapped[bool] = mapped_column(Boolean, default=True)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    sns_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    dashboard_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="demo_budgets", lazy="selectin")

    @property
    def utilization_pct(self) -> float:
        if self.amount <= 0:
            return 0.0
        return round((self.spent / self.amount) * 100, 1)

    @property
    def status(self) -> str:
        pct = self.utilization_pct
        if pct >= 100:
            return "exceeded"
        elif pct >= 90:
            return "critical"
        elif pct >= 80:
            return "warning"
        elif pct >= 50:
            return "caution"
        return "healthy"

    def __repr__(self) -> str:
        return f"<DemoBudget {self.name} ${self.amount}>"


class AWSBudget(Base, TimestampMixin):
    __tablename__ = "aws_budgets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    period: Mapped[str] = mapped_column(String(20), default="monthly")  # daily, weekly, monthly
    spent: Mapped[float] = mapped_column(Float, default=0.0)
    alert_threshold_50: Mapped[bool] = mapped_column(Boolean, default=True)
    alert_threshold_80: Mapped[bool] = mapped_column(Boolean, default=True)
    alert_threshold_90: Mapped[bool] = mapped_column(Boolean, default=True)
    alert_threshold_100: Mapped[bool] = mapped_column(Boolean, default=True)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    sns_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    dashboard_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="aws_budgets", lazy="selectin")

    @property
    def utilization_pct(self) -> float:
        if self.amount <= 0:
            return 0.0
        return round((self.spent / self.amount) * 100, 1)

    @property
    def status(self) -> str:
        pct = self.utilization_pct
        if pct >= 100:
            return "exceeded"
        elif pct >= 90:
            return "critical"
        elif pct >= 80:
            return "warning"
        elif pct >= 50:
            return "caution"
        return "healthy"

    def __repr__(self) -> str:
        return f"<AWSBudget {self.name} ${self.amount}>"
