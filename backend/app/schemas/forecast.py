"""Forecast schemas."""

from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime


class ForecastResponse(BaseModel):
    id: str
    horizon: str
    forecast_date: date
    predicted_amount: float
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    confidence: float
    service: Optional[str] = None
    model_used: str
    generated_at: datetime

    model_config = {"from_attributes": True}


class ForecastSummary(BaseModel):
    next_day: Optional[ForecastResponse] = None
    next_week: Optional[ForecastResponse] = None
    next_month: Optional[ForecastResponse] = None
    next_quarter: Optional[ForecastResponse] = None
    end_of_year: Optional[ForecastResponse] = None
    trend_data: List[dict] = []


class ForecastRequest(BaseModel):
    horizon: str = "month"  # day, week, month, quarter, year
    service: Optional[str] = None  # None = all services
