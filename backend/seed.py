"""
CloudWise AI - Database Seeding Module
Generates comprehensive cost data, budgets, recommendations, active anomalies,
and forecasts for registered user accounts. Zero hardcoded demo credentials.
"""
import json
import sys
import os
import random
from datetime import date, datetime, timedelta, timezone

# Add parent directory to path to allow imports from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import Base, engine, SessionLocal, init_db
from app.models.organization import Organization
from app.models.user import User
from app.models.aws_account import AWSAccount
from app.models.cost_record import CostRecord
from app.models.budget import Budget
from app.models.anomaly import Anomaly
from app.models.recommendation import Recommendation
from app.models.forecast import Forecast
from app.models.settings import UserSettings


def seed_user_data(user, db):
    """Seed financial records, anomalies, budgets, and recommendations for a user."""
    # 1. Ensure user has organization
    org = user.organization
    if not org:
        org_name = f"{user.full_name}'s Organization"
        slug = org_name.lower().replace(" ", "-").replace("'", "")
        org = Organization(name=org_name, slug=slug)
        db.add(org)
        db.commit()
        db.refresh(org)
        user.org_id = org.id
        db.commit()

    # 2. Ensure User Settings
    settings = db.query(UserSettings).filter_by(user_id=user.id).first()
    if not settings:
        settings = UserSettings(
            user_id=user.id,
            theme="dark",
            currency="USD",
            email_alerts=True,
            slack_alerts=False,
            weekly_reports=True
        )
        db.add(settings)
        db.commit()

    # 3. Create or reuse AWS Account for user's organization
    account = db.query(AWSAccount).filter_by(org_id=org.id).first()
    if not account:
        # Check if this account_id already exists globally (UNIQUE constraint)
        existing_account = db.query(AWSAccount).filter_by(account_id="123456789012").first()
        if existing_account:
            account = existing_account
        else:
            account = AWSAccount(
                org_id=org.id,
                account_id="123456789012",
                account_name="Production Root",
                role_arn="arn:aws:iam::123456789012:role/CloudWiseReadOnlyRole",
                external_id=f"ext-{user.id[:8]}",
                region="us-east-1",
                is_active=True
            )
            db.add(account)
            db.commit()
            db.refresh(account)

    # Check if user already has cost records
    existing_records = db.query(CostRecord).filter_by(user_id=user.id).count()
    if existing_records > 0:
        print(f"[INFO] User {user.email} already has {existing_records} cost records.")
        return

    print(f"[PROCESS] Generating 90 days of cost records for {user.email}...")
    today = date.today()
    start_date = today - timedelta(days=90)

    # Baseline cost profiles
    services = [
        {"name": "Amazon EC2", "base": 80.0, "var": 10.0, "region": "us-east-1"},
        {"name": "Amazon RDS", "base": 40.0, "var": 2.0, "region": "us-east-1"},
        {"name": "Amazon S3", "base": 15.0, "var": 0.5, "region": "us-west-2"},
        {"name": "AWS Lambda", "base": 10.0, "var": 3.0, "region": "eu-west-1"},
        {"name": "Amazon CloudFront", "base": 8.0, "var": 1.5, "region": "us-east-1"},
        {"name": "Amazon DynamoDB", "base": 6.0, "var": 0.5, "region": "ap-southeast-1"}
    ]

    random.seed(42)  # For deterministic baseline generation

    cost_records = []
    current_date = start_date
    while current_date <= today:
        day_factor = 0.8 if current_date.weekday() >= 5 else 1.0
        
        for svc in services:
            spike = 0.0
            if svc["name"] == "Amazon EC2" and current_date == (today - timedelta(days=12)):
                spike = 650.0

            amount = (svc["base"] + random.uniform(-svc["var"], svc["var"])) * day_factor + spike
            amount = round(amount, 2)
            usage = round(amount * random.uniform(0.9, 1.1), 2)

            cr = CostRecord(
                aws_account_id=account.id,
                user_id=user.id,
                date=current_date,
                service=svc["region"],
                region=svc["region"],
                amount=amount,
                usage_quantity=usage,
                granularity="DAILY",
                ingested_at=datetime.now(timezone.utc) - timedelta(days=(today - current_date).days)
            )
            # Correct service name attribute
            cr.service = svc["name"]
            cost_records.append(cr)

        current_date += timedelta(days=1)

    db.bulk_save_objects(cost_records)
    db.commit()

    # Find the EC2 spike record to link the anomaly
    spike_date = today - timedelta(days=12)
    ec2_spike_record = (
        db.query(CostRecord)
        .filter(
            CostRecord.user_id == user.id,
            CostRecord.service == "Amazon EC2",
            CostRecord.date == spike_date
        )
        .first()
    )

    if ec2_spike_record:
        anomaly1 = Anomaly(
            cost_record_id=ec2_spike_record.id,
            date=spike_date,
            service="Amazon EC2",
            severity="critical",
            impact_amount=650.00,
            root_cause="Unscheduled GPU instance scale-out during batch job execution",
            detection_method="z_score",
            confidence_score=0.98,
            is_resolved=False,
            details=json.dumps({
                "expected_cost": 85.0,
                "actual_cost": 735.0,
                "spike_ratio": 8.6,
                "region": "us-east-1"
            }),
            detected_at=datetime.now(timezone.utc) - timedelta(days=12)
        )
        db.add(anomaly1)
        db.commit()

    # Seed Budgets
    budgets_data = [
        {
            "name": "Production Infrastructure",
            "amount": 4500.00,
            "period": "monthly",
            "spent": 3280.50,
            "alert_threshold_50": True,
            "alert_threshold_80": True,
            "alert_threshold_90": True,
            "alert_threshold_100": True,
            "email_enabled": True,
            "dashboard_enabled": True,
            "is_active": True
        },
        {
            "name": "Data Analytics & ML Pipeline",
            "amount": 1500.00,
            "period": "monthly",
            "spent": 1420.00,
            "alert_threshold_50": True,
            "alert_threshold_80": True,
            "alert_threshold_90": True,
            "alert_threshold_100": True,
            "email_enabled": True,
            "dashboard_enabled": True,
            "is_active": True
        },
        {
            "name": "Staging & Dev Testbed",
            "amount": 800.00,
            "period": "monthly",
            "spent": 340.20,
            "alert_threshold_50": True,
            "alert_threshold_80": True,
            "alert_threshold_90": False,
            "alert_threshold_100": True,
            "email_enabled": False,
            "dashboard_enabled": True,
            "is_active": True
        }
    ]

    for b_data in budgets_data:
        budget = Budget(user_id=user.id, **b_data)
        db.add(budget)
    db.commit()

    # Seed Recommendations
    recs_data = [
        {
            "service": "Amazon EC2",
            "resource_id": "i-0a8b9c1d2e3f4a5b6",
            "resource_type": "instance",
            "category": "rightsizing",
            "recommendation": "Rightsize EC2 instance i-0a8b9c1d2e3f4a5b6 in us-east-1 from m5.2xlarge to m5.xlarge based on 14-day average CPU utilization (< 12%).",
            "current_cost": 280.00,
            "optimized_cost": 140.00,
            "monthly_savings": 140.00,
            "annual_savings": 1680.00,
            "priority": "high",
            "status": "pending",
            "difficulty": "easy"
        },
        {
            "service": "Amazon RDS",
            "resource_id": "db-analytics-prod",
            "resource_type": "database",
            "category": "idle",
            "recommendation": "DB Instance db-analytics-prod in us-east-1 (db.r5.2xlarge) is idle. Migrate to db.t3.medium or pause on weekends.",
            "current_cost": 450.00,
            "optimized_cost": 110.00,
            "monthly_savings": 340.00,
            "annual_savings": 4080.00,
            "priority": "critical",
            "status": "pending",
            "difficulty": "medium"
        },
        {
            "service": "Amazon S3",
            "resource_id": "raw-logs-bucket",
            "resource_type": "bucket",
            "category": "lifecycle",
            "recommendation": "Add S3 Lifecycle rule to transition objects in raw-logs-bucket older than 30 days to S3 Intelligent-Tiering or Glacier Deep Archive.",
            "current_cost": 210.00,
            "optimized_cost": 50.00,
            "monthly_savings": 160.00,
            "annual_savings": 1920.00,
            "priority": "medium",
            "status": "pending",
            "difficulty": "easy"
        }
    ]

    for r_data in recs_data:
        rec = Recommendation(user_id=user.id, **r_data)
        db.add(rec)
    db.commit()

    # Seed Forecasts
    forecasts_data = [
        {
            "horizon": "day",
            "forecast_date": today + timedelta(days=1),
            "predicted_amount": 165.20,
            "lower_bound": 150.00,
            "upper_bound": 180.00,
            "confidence": 0.95,
            "model_used": "statistical_ensemble"
        },
        {
            "horizon": "week",
            "forecast_date": today + timedelta(days=7),
            "predicted_amount": 1150.00,
            "lower_bound": 1050.00,
            "upper_bound": 1250.00,
            "confidence": 0.95,
            "model_used": "statistical_ensemble"
        },
        {
            "horizon": "month",
            "forecast_date": today + timedelta(days=30),
            "predicted_amount": 4920.00,
            "lower_bound": 4500.00,
            "upper_bound": 5300.00,
            "confidence": 0.95,
            "model_used": "statistical_ensemble"
        },
        {
            "horizon": "quarter",
            "forecast_date": today + timedelta(days=90),
            "predicted_amount": 14850.00,
            "lower_bound": 13500.00,
            "upper_bound": 16200.00,
            "confidence": 0.95,
            "model_used": "statistical_ensemble"
        }
    ]

    for f_data in forecasts_data:
        f = Forecast(user_id=user.id, **f_data)
        db.add(f)
    db.commit()
    print(f"[SUCCESS] Financial & FinOps data initialized for {user.email}")


def seed_database():
    """Seed cost & analytics data for all registered users."""
    print("[RUNNING] Initializing database...")
    init_db()
    db = SessionLocal()

    try:
        users = db.query(User).all()
        if not users:
            print("[INFO] No registered users found in database.")
            print("[INFO] Please register a new account at http://localhost:5173/register")
            return

        for user in users:
            seed_user_data(user, db)

        print("[COMPLETE] Database seeding completed cleanly!")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error seeding database: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
