"""Scheduled Celery tasks for AWS cost ingestion and anomaly detection."""

from datetime import datetime, timedelta, timezone
from app.celery_worker import celery_app
from app.services.aws_cost_explorer import fetch_aws_cost_and_usage
from app.ai.anomaly_detector import AnomalyDetector
from app.database import SessionLocal
from app.models.aws_account import AWSAccount
from app.models.user import User
from app.models.cost_record import CostRecord


@celery_app.task(bind=True, max_retries=3)
def fetch_and_store_aws_costs(self):
    """Fetch recent AWS costs (Mocked for standalone demo)."""
    return "Skipped live AWS fetch (standalone demo mode)"


@celery_app.task(bind=True, max_retries=3)
def run_anomaly_detection(self):
    """Run ML anomaly detection for active users."""
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active.is_(True)).all()
        for user in users:
            detector = AnomalyDetector(db)
            detector.detect_anomalies(user.id)
    except Exception as e:
        raise self.retry(exc=e, countdown=60)
    finally:
        db.close()
