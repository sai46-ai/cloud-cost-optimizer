"""Cost Record model - stores AWS cost data ingested from Cost Explorer."""

from sqlalchemy import String, Float, Date, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime
from app.database import Base
from app.models.base import generate_uuid, utc_now


class CostRecord(Base):
    __tablename__ = "cost_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    aws_account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("aws_accounts.id"), nullable=True, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True, index=True
    )
    date: Mapped[datetime.date] = mapped_column(Date, index=True, nullable=False)
    service: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    region: Mapped[str] = mapped_column(String(50), nullable=True, default="us-east-1")
    amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    usage_quantity: Mapped[float] = mapped_column(Float, nullable=True, default=0.0)
    usage_type: Mapped[str] = mapped_column(String(255), nullable=True)
    granularity: Mapped[str] = mapped_column(
        String(20), default="DAILY"
    )  # DAILY, MONTHLY
    ingested_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    aws_account = relationship(
        "AWSAccount", back_populates="cost_records", lazy="selectin"
    )
    user = relationship("User", back_populates="cost_records", lazy="selectin")
    anomaly = relationship(
        "Anomaly", back_populates="cost_record", uselist=False, lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<CostRecord {self.date} {self.service} ${self.amount:.2f}>"


class DemoCostRecord(Base):
    __tablename__ = "demo_cost_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    date: Mapped[datetime.date] = mapped_column(Date, index=True, nullable=False)
    service: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    region: Mapped[str] = mapped_column(String(50), nullable=True, default="us-east-1")
    amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    usage_quantity: Mapped[float] = mapped_column(Float, nullable=True, default=0.0)
    usage_type: Mapped[str] = mapped_column(String(255), nullable=True)
    granularity: Mapped[str] = mapped_column(String(20), default="DAILY")
    ingested_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="demo_cost_records", lazy="selectin")
    anomaly = relationship("DemoAnomaly", back_populates="cost_record", uselist=False, lazy="selectin")

    def __repr__(self) -> str:
        return f"<DemoCostRecord {self.date} {self.service} ${self.amount:.2f}>"


class AWSCostRecord(Base):
    __tablename__ = "aws_cost_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    aws_account_id: Mapped[str] = mapped_column(String(36), ForeignKey("aws_accounts.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    date: Mapped[datetime.date] = mapped_column(Date, index=True, nullable=False)
    service: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    region: Mapped[str] = mapped_column(String(50), nullable=True, default="us-east-1")
    amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    usage_quantity: Mapped[float] = mapped_column(Float, nullable=True, default=0.0)
    usage_type: Mapped[str] = mapped_column(String(255), nullable=True)
    granularity: Mapped[str] = mapped_column(String(20), default="DAILY")
    ingested_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    aws_account = relationship("AWSAccount", back_populates="aws_cost_records", lazy="selectin")
    user = relationship("User", back_populates="aws_cost_records", lazy="selectin")
    anomaly = relationship("AWSAnomaly", back_populates="cost_record", uselist=False, lazy="selectin")

    def __repr__(self) -> str:
        return f"<AWSCostRecord {self.date} {self.service} ${self.amount:.2f}>"
