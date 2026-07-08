"""Anomaly API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.ai.anomaly_detector import AnomalyDetector
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.anomaly import AnomalyResponse, AnomalySummary
from typing import List

router = APIRouter()


@router.get("/", response_model=List[AnomalyResponse])
def get_anomalies(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """Get detected cost anomalies."""
    detector = AnomalyDetector(db)
    return detector.get_anomalies(user.id)


@router.get("/summary", response_model=AnomalySummary)
def get_anomaly_summary(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """Get anomaly summary statistics."""
    detector = AnomalyDetector(db)
    return detector.get_anomaly_summary(user.id)


@router.post("/detect", response_model=dict)
def run_detection(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """Trigger anomaly detection manually."""
    detector = AnomalyDetector(db)
    anomalies = detector.detect_anomalies(user.id)
    return {
        "message": f"Detection complete. Found {len(anomalies)} new anomalies.",
        "count": len(anomalies),
    }
