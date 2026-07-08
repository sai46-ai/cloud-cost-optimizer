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
    """Fetch recent AWS costs for active accounts and store in DB."""
    db = SessionLocal()
    try:
        # Get active AWS accounts
        accounts = db.query(AWSAccount).filter(AWSAccount.is_active.is_(True)).all()
        for account in accounts:
            # Find an active user in the organization to associate cost records with
            user = (
                db.query(User)
                .filter(User.org_id == account.org_id, User.is_active.is_(True))
                .first()
            )
            if not user:
                continue

            # Fetch AWS costs for the last 7 days
            today = datetime.now(timezone.utc).date()
            start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
            end_date = today.strftime("%Y-%m-%d")

            records = fetch_aws_cost_and_usage(start_date, end_date)
            for r in records:
                # Check if this record already exists
                exists = (
                    db.query(CostRecord)
                    .filter_by(
                        aws_account_id=account.id,
                        user_id=user.id,
                        date=r["date"],
                        service=r["service"],
                    )
                    .first()
                )
                if not exists:
                    cr = CostRecord(
                        aws_account_id=account.id,
                        user_id=user.id,
                        date=r["date"],
                        service=r["service"],
                        region=account.region or "us-east-1",
                        amount=r["amount"],
                        usage_quantity=r["usage"],
                        granularity="DAILY",
                    )
                    db.add(cr)
        db.commit()
    except Exception as e:
        db.rollback()
        raise self.retry(exc=e, countdown=60)
    finally:
        db.close()


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
