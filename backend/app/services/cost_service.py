"""
Cost Service
Business logic for cost data retrieval, analysis, and dashboard metrics.
Includes realistic demo data generation for portfolio showcase.
"""

from datetime import date, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.cost_record import CostRecord
from app.repositories.cost_repository import CostRepository
from app.schemas.cost import (
    DashboardMetrics,
    ServiceCost,
    RegionCost,
    CostTrend,
    CostBreakdown,
)

# Realistic AWS service names and cost profiles for demo
AWS_SERVICES = [
    ("Amazon EC2", 2800, 400),
    ("Amazon RDS", 1200, 200),
    ("Amazon S3", 450, 80),
    ("AWS Lambda", 320, 60),
    ("Amazon CloudFront", 280, 50),
    ("Amazon DynamoDB", 180, 40),
    ("Amazon ElastiCache", 150, 30),
    ("AWS Data Transfer", 120, 25),
    ("Amazon SQS", 45, 10),
    ("Amazon SNS", 25, 8),
    ("Amazon CloudWatch", 65, 15),
    ("AWS KMS", 30, 5),
]

AWS_REGIONS = [
    ("us-east-1", 0.40),
    ("us-west-2", 0.25),
    ("eu-west-1", 0.15),
    ("ap-southeast-1", 0.10),
    ("eu-central-1", 0.07),
    ("ap-northeast-1", 0.03),
]


class CostService:
    def __init__(self, db: Session):
        self.db = db
        self.cost_repo = CostRepository(db)

    def get_dashboard_metrics(self, user_id: str) -> DashboardMetrics:
        """Get all key metrics for the executive dashboard."""
        today = date.today()
        month_start = today.replace(day=1)
        prev_month_end = month_start - timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)

        # Current month spend
        mtd_spend = self.cost_repo.get_total_by_date_range(user_id, month_start, today)
        prev_month_spend = self.cost_repo.get_total_by_date_range(
            user_id, prev_month_start, prev_month_end
        )

        # Calculate change percentage
        change_pct = 0.0
        if prev_month_spend > 0:
            change_pct = round(
                ((mtd_spend - prev_month_spend) / prev_month_spend) * 100, 1
            )

        # Daily average
        days_elapsed = max((today - month_start).days, 1)
        daily_avg = round(mtd_spend / days_elapsed, 2)

        # Forecasted month end
        days_in_month = 30
        forecasted = round(daily_avg * days_in_month, 2)

        # Top services and regions
        top_services = self.cost_repo.get_top_services(
            user_id, month_start, today, limit=6
        )
        top_regions = self.cost_repo.get_top_regions(
            user_id, month_start, today, limit=6
        )

        # Daily costs for chart
        thirty_days_ago = today - timedelta(days=30)
        daily_costs = self.cost_repo.get_daily_totals(user_id, thirty_days_ago, today)
        monthly_costs = self.cost_repo.get_monthly_totals(user_id, 12)

        # Count unresolved anomalies dynamically
        from app.models.anomaly import Anomaly
        from sqlalchemy import func

        active_anomalies_count = (
            self.db.query(func.count(Anomaly.id))
            .join(CostRecord, Anomaly.cost_record_id == CostRecord.id)
            .filter(CostRecord.user_id == user_id, Anomaly.is_resolved.is_(False))
            .scalar()
        )

        return DashboardMetrics(
            total_spend_mtd=round(mtd_spend, 2),
            total_spend_prev_month=round(prev_month_spend, 2),
            spend_change_pct=change_pct,
            daily_spend_avg=daily_avg,
            forecasted_month_end=forecasted,
            total_savings_opportunity=round(
                mtd_spend * 0.23, 2
            ),  # ~23% typical optimization
            active_anomalies=active_anomalies_count,
            budget_health_pct=72.5,
            top_services=[ServiceCost(**s) for s in top_services],
            top_regions=[RegionCost(**r) for r in top_regions],
            daily_costs=[CostTrend(**d) for d in daily_costs],
            monthly_costs=[CostTrend(**m) for m in monthly_costs],
        )

    def get_cost_breakdown(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> CostBreakdown:
        """Get detailed cost breakdown by service and region."""
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        by_service = self.cost_repo.get_top_services(user_id, start_date, end_date)
        by_region = self.cost_repo.get_top_regions(user_id, start_date, end_date)
        daily_trend = self.cost_repo.get_daily_totals(user_id, start_date, end_date)
        total = self.cost_repo.get_total_by_date_range(user_id, start_date, end_date)

        return CostBreakdown(
            by_service=[ServiceCost(**s) for s in by_service],
            by_region=[RegionCost(**r) for r in by_region],
            daily_trend=[CostTrend(**d) for d in daily_trend],
            total=round(total, 2),
        )

    def get_costs(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        service: Optional[str] = None,
    ) -> List[dict]:
        """Get raw cost records with optional filters."""
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        records = self.cost_repo.get_by_date_range(
            user_id, start_date, end_date, service
        )
        return [
            {
                "id": r.id,
                "date": r.date,
                "service": r.service,
                "region": r.region,
                "amount": round(r.amount, 2),
                "usage_quantity": r.usage_quantity,
                "granularity": r.granularity,
                "ingested_at": r.ingested_at,
            }
            for r in records
        ]
