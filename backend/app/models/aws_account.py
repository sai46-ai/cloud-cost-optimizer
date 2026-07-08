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

    # Relationships
    organization = relationship(
        "Organization", back_populates="aws_accounts", lazy="selectin"
    )
    cost_records = relationship(
        "CostRecord", back_populates="aws_account", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<AWSAccount {self.account_id}>"
