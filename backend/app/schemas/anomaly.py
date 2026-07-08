"""Anomaly schemas."""

from typing import Optional
from pydantic import BaseModel
from datetime import datetime, date


class AnomalyResponse(BaseModel):
    id: str
    date: date
    service: str
    severity: str
    impact_amount: float
    root_cause: Optional[str] = None
    detection_method: str
    confidence_score: float
    is_resolved: bool
    details: Optional[str] = None
    detected_at: datetime

    model_config = {"from_attributes": True}


class AnomalySummary(BaseModel):
    total_anomalies: int
    critical: int
    high: int
    medium: int
    low: int
    total_impact: float
    unresolved: int
