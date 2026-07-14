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
from app.models.user import User, DemoUser
from app.models.aws_account import AWSAccount, DemoAlert, AWSAlert
from app.models.cost_record import CostRecord, DemoCostRecord, AWSCostRecord
from app.models.budget import Budget, DemoBudget, AWSBudget
from app.models.anomaly import Anomaly, DemoAnomaly, AWSAnomaly
from app.models.recommendation import Recommendation, DemoRecommendation, AWSRecommendation
from app.models.forecast import Forecast, DemoForecast, AWSForecast
from app.models.report import Report, DemoReport, AWSReport
from app.models.settings import UserSettings


def seed_user_data(user, db):
    """Seed financial records, anomalies, budgets, and recommendations for a user in Demo tables."""
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

    # 3. Ensure DemoUser
    demo_user = db.query(DemoUser).filter_by(user_id=user.id).first()
    if not demo_user:
        demo_user = DemoUser(
            user_id=user.id,
            full_name=user.full_name,
            email=user.email,
            role=user.role,
            is_active=True
        )
        db.add(demo_user)
        db.commit()

    # Check if user already has demo cost records
    existing_records = db.query(DemoCostRecord).filter_by(user_id=user.id).count()
    if existing_records > 0:
        print(f"[INFO] User {user.email} already has {existing_records} demo cost records.")
        return

    print(f"[PROCESS] Generating 90 days of deterministic demo cost records for {user.email}...")
    today = date.today()
    start_date = today - timedelta(days=90)

    # Baseline cost profiles
    services = [
        {"name": "Amazon EC2", "base": 80.0, "region": "us-east-1"},
        {"name": "Amazon RDS", "base": 40.0, "region": "us-east-1"},
        {"name": "Amazon S3", "base": 15.0, "region": "us-west-2"},
        {"name": "AWS Lambda", "base": 10.0, "region": "eu-west-1"},
        {"name": "Amazon CloudFront", "base": 8.0, "region": "us-east-1"},
        {"name": "Amazon DynamoDB", "base": 6.0, "region": "ap-southeast-1"}
    ]

    cost_records = []
    current_date = start_date
    while current_date <= today:
        day_factor = 0.8 if current_date.weekday() >= 5 else 1.0
        
        for svc in services:
            spike = 0.0
            if svc["name"] == "Amazon EC2" and current_date == (today - timedelta(days=12)):
                spike = 650.0

            amount = round(svc["base"] * day_factor + spike, 2)
            usage = round(amount * 1.05, 2)

            cr = DemoCostRecord(
                user_id=user.id,
                date=current_date,
                service=svc["name"],
                region=svc["region"],
                amount=amount,
                usage_quantity=usage,
                granularity="DAILY",
                ingested_at=datetime.now(timezone.utc) - timedelta(days=(today - current_date).days)
            )
            cost_records.append(cr)

        current_date += timedelta(days=1)

    db.bulk_save_objects(cost_records)
    db.commit()

    # Find the EC2 spike record to link the anomaly
    spike_date = today - timedelta(days=12)
    ec2_spike_record = (
        db.query(DemoCostRecord)
        .filter(
            DemoCostRecord.user_id == user.id,
            DemoCostRecord.service == "Amazon EC2",
            DemoCostRecord.date == spike_date
        )
        .first()
    )

    if ec2_spike_record:
        anomaly1 = DemoAnomaly(
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
                "expected_cost": 80.0,
                "actual_cost": 730.0,
                "spike_ratio": 9.1,
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
        budget = DemoBudget(user_id=user.id, **b_data)
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
        rec = DemoRecommendation(user_id=user.id, **r_data)
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
        f = DemoForecast(user_id=user.id, **f_data)
        db.add(f)
    db.commit()

    # Seed Reports
    demo_report = DemoReport(
        user_id=user.id,
        report_type="cost_summary",
        format="pdf",
        filename="cloudwise_monthly_cost_summary.pdf",
        file_size=102450.0,
        status="completed",
        generated_at=datetime.now(timezone.utc) - timedelta(days=2)
    )
    db.add(demo_report)
    db.commit()

    # Seed DemoAlerts
    demo_alert = DemoAlert(
        user_id=user.id,
        alert_type="budget",
        title="Budget Alert: Staging & Dev Testbed",
        message="Staging & Dev Testbed has exceeded 50% utilization limit.",
        is_read=False
    )
    db.add(demo_alert)
    db.commit()

    print(f"[SUCCESS] Isolated Demo financial & FinOps data initialized for {user.email}")


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
