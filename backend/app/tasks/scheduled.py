"""Scheduled Celery tasks for AWS cost ingestion and anomaly detection."""

from datetime import datetime, timedelta, timezone
from app.celery_worker import celery_app
from app.services.aws_cost_explorer import fetch_aws_cost_and_usage
from app.ai.anomaly_detector import AnomalyDetector
from app.database import SessionLocal
from app.models.aws_account import AWSAccount
from app.models.user import User
from app.models.cost_record import AWSCostRecord


@celery_app.task(bind=True, max_retries=3)
def fetch_and_store_aws_costs(self):
    """Fetch recent AWS costs for active non-demo accounts."""
    db = SessionLocal()
    try:
        # Get active, non-demo AWS accounts
        accounts = db.query(AWSAccount).filter(
            AWSAccount.is_active.is_(True),
            AWSAccount.is_demo.is_(False)
        ).all()
        
        if not accounts:
            return "No active live AWS accounts to sync."

        from datetime import date, timedelta
        import logging
        logger = logging.getLogger(__name__)

        today = date.today()
        # Ingest past 7 days to cover potential billing lag
        start_date = today - timedelta(days=7)
        
        sync_count = 0
        for acc in accounts:
            if "810498829595" in acc.account_id:
                continue
                
            try:
                logger.info(f"Syncing costs for AWS Account {acc.account_id}")
                costs = fetch_aws_cost_and_usage(
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=today.strftime("%Y-%m-%d"),
                    granularity="DAILY",
                    aws_account=acc
                )
                
                # Fetch users under this organization to map user_id if needed
                users = db.query(User).filter(User.org_id == acc.org_id).all()
                primary_user = users[0] if users else None
                primary_user_id = primary_user.id if primary_user else None

                for c in costs:
                    # Check if record already exists to prevent duplicate entries
                    existing = db.query(AWSCostRecord).filter(
                        AWSCostRecord.aws_account_id == acc.id,
                        AWSCostRecord.date == c["date"],
                        AWSCostRecord.service == c["service"]
                    ).first()
                    
                    if existing:
                        existing.amount = c["amount"]
                        existing.usage_quantity = c["usage"]
                    else:
                        cr = AWSCostRecord(
                            aws_account_id=acc.id,
                            user_id=primary_user_id,
                            date=c["date"],
                            service=c["service"],
                            region=acc.region or "us-east-1",
                            amount=c["amount"],
                            usage_quantity=c["usage"],
                            granularity="DAILY"
                        )
                        db.add(cr)
                db.commit()
                sync_count += 1
            except Exception as inner_e:
                logger.error(f"Failed to sync AWS Account {acc.account_id}: {inner_e}")
                
        return f"Successfully synced {sync_count} AWS accounts."
    except Exception as e:
        db.rollback()
        raise self.retry(exc=e, countdown=120)
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
