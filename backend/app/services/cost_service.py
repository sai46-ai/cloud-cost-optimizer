"""
Cost Service
Business logic for cost data retrieval, analysis, and dashboard metrics.
Includes realistic demo data generation for portfolio showcase.
"""

from datetime import date, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.cost_record import CostRecord
from app.models.user import User
from app.models.aws_account import AWSAccount
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
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            from app.core.exceptions import EntityNotFoundError
            raise EntityNotFoundError("User", user_id)

        # 1. Reviewer Account (Demo Mode)
        if user.is_demo_mode:
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

            # Get savings opportunity from recommendations
            from app.services.recommendation_service import RecommendationService
            rec_summary = RecommendationService(self.db).get_recommendation_summary(user_id)
            savings_opportunity = rec_summary.get("total_monthly_savings", 0.0)

            return DashboardMetrics(
                total_spend_mtd=round(mtd_spend, 2),
                total_spend_prev_month=round(prev_month_spend, 2),
                spend_change_pct=change_pct,
                daily_spend_avg=daily_avg,
                forecasted_month_end=forecasted,
                total_savings_opportunity=savings_opportunity,
                active_anomalies=active_anomalies_count,
                budget_health_pct=72.5,
                top_services=[ServiceCost(**s) for s in top_services],
                top_regions=[RegionCost(**r) for r in top_regions],
                daily_costs=[CostTrend(**d) for d in daily_costs],
                monthly_costs=[CostTrend(**m) for m in monthly_costs],
                aws_connection_failed=False
            )

        # 2. Normal User
        else:
            if not user.is_aws_connected:
                # Onboarding state: return empty dashboard metrics immediately without fabricated data.
                return DashboardMetrics(
                    total_spend_mtd=0.0,
                    total_spend_prev_month=0.0,
                    spend_change_pct=0.0,
                    daily_spend_avg=0.0,
                    forecasted_month_end=0.0,
                    total_savings_opportunity=0.0,
                    active_anomalies=0,
                    budget_health_pct=100.0,
                    top_services=[],
                    top_regions=[],
                    daily_costs=[],
                    monthly_costs=[],
                    aws_connection_failed=False
                )
            
            # Fetch live AWS metrics
            aws_account = self.db.query(AWSAccount).filter(AWSAccount.org_id == user.org_id, AWSAccount.is_active.is_(True)).first()
            if not aws_account:
                return DashboardMetrics(
                    total_spend_mtd=0.0,
                    total_spend_prev_month=0.0,
                    spend_change_pct=0.0,
                    daily_spend_avg=0.0,
                    forecasted_month_end=0.0,
                    total_savings_opportunity=0.0,
                    active_anomalies=0,
                    budget_health_pct=100.0,
                    top_services=[],
                    top_regions=[],
                    daily_costs=[],
                    monthly_costs=[],
                    aws_connection_failed=False
                )

            from app.services.aws_cost_explorer import cost_explorer_service
            try:
                live_metrics = cost_explorer_service.get_live_dashboard_metrics(aws_account)

                # Get savings opportunity dynamically from live recommendations
                from app.services.recommendation_service import RecommendationService
                rec_service = RecommendationService(self.db)
                rec_summary = rec_service.get_recommendation_summary(user_id)
                savings_opportunity = rec_summary.get("total_monthly_savings", 0.0)

                # Calculate active anomalies dynamically
                from app.ai.anomaly_detector import AnomalyDetector
                active_anomalies_count = len(AnomalyDetector(self.db).get_anomalies(user_id))

                # Budget health
                from app.services.budget_service import BudgetService
                budgets = BudgetService(self.db).get_budgets(user_id)
                healthy_count = sum(1 for b in budgets if b.spent <= b.amount)
                budget_health_pct = (healthy_count / len(budgets)) * 100 if budgets else 100.0

                return DashboardMetrics(
                    total_spend_mtd=live_metrics["total_spend_mtd"],
                    total_spend_prev_month=live_metrics["total_spend_prev_month"],
                    spend_change_pct=live_metrics["spend_change_pct"],
                    daily_spend_avg=live_metrics["daily_spend_avg"],
                    forecasted_month_end=live_metrics["forecasted_month_end"],
                    total_savings_opportunity=savings_opportunity,
                    active_anomalies=active_anomalies_count,
                    budget_health_pct=budget_health_pct,
                    top_services=[ServiceCost(**s) for s in live_metrics["top_services"]],
                    top_regions=[RegionCost(**r) for r in live_metrics["top_regions"]],
                    daily_costs=[CostTrend(**d) for d in live_metrics["daily_costs"]],
                    monthly_costs=[CostTrend(**m) for m in live_metrics["monthly_costs"]],
                    aws_connection_failed=False
                )
            except Exception as e:
                import logging
                logger = logging.getLogger("cloudwise")
                logger.warning("AWS Cost Explorer metrics fetch failed: %s. Falling back to local database cost data.", e)

                # Fallback to local DB records calculations
                today = date.today()
                month_start = today.replace(day=1)
                prev_month_end = month_start - timedelta(days=1)
                prev_month_start = prev_month_end.replace(day=1)

                mtd_spend = self.cost_repo.get_total_by_date_range(user_id, month_start, today)
                prev_month_spend = self.cost_repo.get_total_by_date_range(
                    user_id, prev_month_start, prev_month_end
                )

                change_pct = 0.0
                if prev_month_spend > 0:
                    change_pct = round(
                        ((mtd_spend - prev_month_spend) / prev_month_spend) * 100, 1
                    )

                days_elapsed = max((today - month_start).days, 1)
                daily_avg = round(mtd_spend / days_elapsed, 2)
                days_in_month = 30
                forecasted = round(daily_avg * days_in_month, 2)

                top_services = self.cost_repo.get_top_services(user_id, month_start, today, limit=6)
                top_regions = self.cost_repo.get_top_regions(user_id, month_start, today, limit=6)

                thirty_days_ago = today - timedelta(days=30)
                daily_costs = self.cost_repo.get_daily_totals(user_id, thirty_days_ago, today)
                monthly_costs = self.cost_repo.get_monthly_totals(user_id, 12)

                from app.models.anomaly import Anomaly
                from sqlalchemy import func
                active_anomalies_count = (
                    self.db.query(func.count(Anomaly.id))
                    .join(CostRecord, Anomaly.cost_record_id == CostRecord.id)
                    .filter(CostRecord.user_id == user_id, Anomaly.is_resolved.is_(False))
                    .scalar()
                ) or 0

                from app.services.recommendation_service import RecommendationService
                rec_summary = RecommendationService(self.db).get_recommendation_summary(user_id)
                savings_opportunity = rec_summary.get("total_monthly_savings", 0.0)

                return DashboardMetrics(
                    total_spend_mtd=round(mtd_spend, 2),
                    total_spend_prev_month=round(prev_month_spend, 2),
                    spend_change_pct=change_pct,
                    daily_spend_avg=daily_avg,
                    forecasted_month_end=forecasted,
                    total_savings_opportunity=savings_opportunity,
                    active_anomalies=active_anomalies_count,
                    budget_health_pct=72.5,
                    top_services=[ServiceCost(**s) for s in top_services],
                    top_regions=[RegionCost(**r) for r in top_regions],
                    daily_costs=[CostTrend(**d) for d in daily_costs],
                    monthly_costs=[CostTrend(**m) for m in monthly_costs],
                    aws_connection_failed=True
                )

    def get_cost_breakdown(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> CostBreakdown:
        """Get detailed cost breakdown by service and region."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            from app.core.exceptions import EntityNotFoundError
            raise EntityNotFoundError("User", user_id)

        # 1. Reviewer Account (Demo Mode)
        if user.is_demo_mode:
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
                aws_connection_failed=False
            )

        # 2. Normal User
        else:
            if not user.is_aws_connected:
                return CostBreakdown(by_service=[], by_region=[], daily_trend=[], total=0.0, aws_connection_failed=False)

            aws_account = self.db.query(AWSAccount).filter(AWSAccount.org_id == user.org_id, AWSAccount.is_active.is_(True)).first()
            if not aws_account:
                return CostBreakdown(by_service=[], by_region=[], daily_trend=[], total=0.0, aws_connection_failed=False)

            if not end_date:
                end_date = date.today()
            if not start_date:
                start_date = end_date - timedelta(days=30)

            from app.services.aws_cost_explorer import cost_explorer_service
            try:
                live_breakdown = cost_explorer_service.get_live_cost_breakdown(aws_account, start_date, end_date)

                return CostBreakdown(
                    by_service=[ServiceCost(**s) for s in live_breakdown["by_service"]],
                    by_region=[RegionCost(**r) for r in live_breakdown["by_region"]],
                    daily_trend=[CostTrend(**d) for d in live_breakdown["daily_trend"]],
                    total=live_breakdown["total"],
                    aws_connection_failed=False
                )
            except Exception as e:
                import logging
                logger = logging.getLogger("cloudwise")
                logger.warning("AWS Cost Explorer breakdown fetch failed: %s. Falling back to local database cost data.", e)

                # Fallback to local DB records calculations
                by_service = self.cost_repo.get_top_services(user_id, start_date, end_date)
                by_region = self.cost_repo.get_top_regions(user_id, start_date, end_date)
                daily_trend = self.cost_repo.get_daily_totals(user_id, start_date, end_date)
                total = self.cost_repo.get_total_by_date_range(user_id, start_date, end_date)

                return CostBreakdown(
                    by_service=[ServiceCost(**s) for s in by_service],
                    by_region=[RegionCost(**r) for r in by_region],
                    daily_trend=[CostTrend(**d) for d in daily_trend],
                    total=round(total, 2),
                    aws_connection_failed=True
                )

    def get_costs(
        self,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        service: Optional[str] = None,
    ) -> List[dict]:
        """Get raw cost records with optional filters."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            from app.core.exceptions import EntityNotFoundError
            raise EntityNotFoundError("User", user_id)

        # 1. Reviewer Account (Demo Mode)
        if user.is_demo_mode:
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

        # 2. Normal User
        else:
            if not user.is_aws_connected:
                return []

            aws_account = self.db.query(AWSAccount).filter(AWSAccount.org_id == user.org_id, AWSAccount.is_active.is_(True)).first()
            if not aws_account:
                return []

            if not end_date:
                end_date = date.today()
            if not start_date:
                start_date = end_date - timedelta(days=30)

            from app.services.aws_cost_explorer import cost_explorer_service
            try:
                return cost_explorer_service.get_live_costs(aws_account, start_date, end_date, service)
            except Exception as e:
                import logging
                logger = logging.getLogger("cloudwise")
                logger.warning("AWS Cost Explorer raw cost fetch failed: %s. Falling back to local database cost data.", e)

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
