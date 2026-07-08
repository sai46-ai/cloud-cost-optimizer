"""Anomaly model with severity scoring and root cause analysis."""

from sqlalchemy import String, Float, Date, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime
from app.database import Base
from app.models.base import generate_uuid, utc_now


class Anomaly(Base):
    __tablename__ = "anomalies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    cost_record_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cost_records.id"), nullable=True, index=True
    )
    date: Mapped[datetime.date] = mapped_column(Date, index=True, nullable=False)
    service: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(
        String(20), default="medium"
    )  # low, medium, high, critical
    impact_amount: Mapped[float] = mapped_column(Float, default=0.0)
    root_cause: Mapped[str] = mapped_column(String(1000), nullable=True)
    detection_method: Mapped[str] = mapped_column(
        String(50), default="isolation_forest"
    )
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_resolved: Mapped[bool] = mapped_column(default=False)
    details: Mapped[str] = mapped_column(String(2000), nullable=True)
    detected_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    cost_record = relationship("CostRecord", back_populates="anomaly")

    def __repr__(self) -> str:
        return f"<Anomaly {self.service} {self.severity} ${self.impact_amount:.2f}>"
