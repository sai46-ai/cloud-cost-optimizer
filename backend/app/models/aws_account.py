"""AWS Account model for managing connected cloud accounts."""

from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid


class AWSAccount(Base, TimestampMixin):
    __tablename__ = "aws_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    org_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id"), nullable=False
    )
    account_id: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role_arn: Mapped[str] = mapped_column(String(500), nullable=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=True)
    region: Mapped[str] = mapped_column(String(50), default="us-east-1")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")

    # Relationships
    organization = relationship(
        "Organization", back_populates="aws_accounts", lazy="selectin"
    )
    cost_records = relationship(
        "CostRecord", back_populates="aws_account", lazy="selectin"
    )
    aws_cost_records = relationship(
        "AWSCostRecord", back_populates="aws_account", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<AWSAccount {self.account_id}>"


class AWSResource(Base, TimestampMixin):
    __tablename__ = "aws_resources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    aws_account_id: Mapped[str] = mapped_column(String(36), ForeignKey("aws_accounts.id"), nullable=False, index=True)
    resource_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    resource_name: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)  # EC2, S3, RDS, Lambda
    region: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="running")
    details: Mapped[str] = mapped_column(String(2000), nullable=True)

    # Relationships
    aws_account = relationship("AWSAccount", lazy="selectin")

    def __repr__(self) -> str:
        return f"<AWSResource {self.resource_id} {self.resource_type}>"


class AWSBilling(Base, TimestampMixin):
    __tablename__ = "aws_billing"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    aws_account_id: Mapped[str] = mapped_column(String(36), ForeignKey("aws_accounts.id"), nullable=False, index=True)
    billing_period: Mapped[str] = mapped_column(String(50), nullable=False)  # YYYY-MM
    invoice_amount: Mapped[float] = mapped_column(default=0.0)
    tax_amount: Mapped[float] = mapped_column(default=0.0)
    currency: Mapped[str] = mapped_column(String(10), default="USD")

    # Relationships
    aws_account = relationship("AWSAccount", lazy="selectin")

    def __repr__(self) -> str:
        return f"<AWSBilling {self.billing_period} ${self.invoice_amount:.2f}>"


class AWSAlert(Base, TimestampMixin):
    __tablename__ = "aws_alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    alert_type: Mapped[str] = mapped_column(String(50), default="budget")  # budget, anomaly
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    is_read: Mapped[bool] = mapped_column(default=False)

    # Relationships
    user = relationship("User", back_populates="aws_alerts", lazy="selectin")

    def __repr__(self) -> str:
        return f"<AWSAlert {self.title}>"


class DemoAlert(Base, TimestampMixin):
    __tablename__ = "demo_alerts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    alert_type: Mapped[str] = mapped_column(String(50), default="budget")  # budget, anomaly
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    is_read: Mapped[bool] = mapped_column(default=False)

    # Relationships
    user = relationship("User", back_populates="demo_alerts", lazy="selectin")

    def __repr__(self) -> str:
        return f"<DemoAlert {self.title}>"
