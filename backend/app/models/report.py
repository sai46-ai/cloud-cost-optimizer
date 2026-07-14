"""Report model for generated PDF/CSV reports."""

from sqlalchemy import String, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base
from app.models.base import generate_uuid, utc_now


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    report_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # cost_summary, optimization, anomaly
    format: Mapped[str] = mapped_column(
        String(10), nullable=False, default="pdf"
    )  # pdf, csv
    filename: Mapped[str] = mapped_column(String(500), nullable=True)
    s3_key: Mapped[str] = mapped_column(String(500), nullable=True)
    file_size: Mapped[float] = mapped_column(Float, nullable=True)
    schedule: Mapped[str] = mapped_column(
        String(20), nullable=True
    )  # daily, weekly, monthly, on_demand
    parameters: Mapped[dict] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, generating, completed, failed
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="reports")

    def __repr__(self) -> str:
        return f"<Report {self.report_type} {self.format}>"


class DemoReport(Base):
    __tablename__ = "demo_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)  # cost_summary, optimization, anomaly
    format: Mapped[str] = mapped_column(String(10), nullable=False, default="pdf")  # pdf, csv
    filename: Mapped[str] = mapped_column(String(500), nullable=True)
    s3_key: Mapped[str] = mapped_column(String(500), nullable=True)
    file_size: Mapped[float] = mapped_column(Float, nullable=True)
    schedule: Mapped[str] = mapped_column(String(20), nullable=True)  # daily, weekly, monthly, on_demand
    parameters: Mapped[dict] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, generating, completed, failed
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="demo_reports", lazy="selectin")

    def __repr__(self) -> str:
        return f"<DemoReport {self.report_type} {self.format}>"


class AWSReport(Base):
    __tablename__ = "aws_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)  # cost_summary, optimization, anomaly
    format: Mapped[str] = mapped_column(String(10), nullable=False, default="pdf")  # pdf, csv
    filename: Mapped[str] = mapped_column(String(500), nullable=True)
    s3_key: Mapped[str] = mapped_column(String(500), nullable=True)
    file_size: Mapped[float] = mapped_column(Float, nullable=True)
    schedule: Mapped[str] = mapped_column(String(20), nullable=True)  # daily, weekly, monthly, on_demand
    parameters: Mapped[dict] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, generating, completed, failed
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="aws_reports", lazy="selectin")

    def __repr__(self) -> str:
        return f"<AWSReport {self.report_type} {self.format}>"
