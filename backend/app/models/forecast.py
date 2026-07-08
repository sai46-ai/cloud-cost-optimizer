"""Forecast model for AI-predicted cost projections."""

from sqlalchemy import String, Float, Date, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date, datetime
from app.database import Base
from app.models.base import generate_uuid, utc_now


class Forecast(Base):
    __tablename__ = "forecasts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    horizon: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # day, week, month, quarter, year
    forecast_date: Mapped[date] = mapped_column(Date, nullable=False)
    predicted_amount: Mapped[float] = mapped_column(Float, nullable=False)
    lower_bound: Mapped[float] = mapped_column(Float, nullable=True)
    upper_bound: Mapped[float] = mapped_column(Float, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.95)
    service: Mapped[str] = mapped_column(String(255), nullable=True)
    model_used: Mapped[str] = mapped_column(String(50), default="prophet")
    trend_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="forecasts")

    def __repr__(self) -> str:
        return f"<Forecast {self.horizon} ${self.predicted_amount:.2f}>"
