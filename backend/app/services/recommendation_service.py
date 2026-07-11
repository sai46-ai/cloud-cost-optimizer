"""
Recommendation Service
Generates optimization recommendations, rightsizing rules, and detects idle cloud resources.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.recommendation import Recommendation
from app.models.user import User
from app.models.aws_account import AWSAccount
from app.repositories.base import BaseRepository
from datetime import datetime, timedelta
from app.schemas.recommendation import IdleResource, IdleResourceSummary


class RecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.rec_repo = BaseRepository(Recommendation, db)

    async def get_recommendations(
        self, user_id: Optional[str] = None
    ) -> List[Recommendation]:
        if not user_id:
            return []
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []

        # 1. Reviewer Account (Demo Mode)
        if user.is_demo_mode:
            recs = (
                self.db.query(Recommendation)
                .filter(Recommendation.user_id == user_id)
                .all()
            )
            if not recs:
                self._generate_default_recommendations(user_id)
                recs = (
                    self.db.query(Recommendation)
                    .filter(Recommendation.user_id == user_id)
                    .all()
                )
            return recs

        # 2. Normal User
        else:
            if not user.is_aws_connected:
                return []
            aws_account = self.db.query(AWSAccount).filter(AWSAccount.org_id == user.org_id, AWSAccount.is_active.is_(True)).first()
            if not aws_account:
                return []

            from app.services.aws_cost_explorer import cost_explorer_service
            raw_recs = cost_explorer_service.fetch_live_rightsizing_recommendations(aws_account)
            
            recs_objs = []
            for r in raw_recs:
                recs_objs.append(
                    Recommendation(
                        id=r["resource_id"],
                        user_id=user_id,
                        service=r["service"],
                        resource_id=r["resource_id"],
                        resource_type=r["resource_type"],
                        category=r["category"],
                        recommendation=r["recommendation"],
                        current_cost=r["current_cost"],
                        optimized_cost=r["optimized_cost"],
                        monthly_savings=r["monthly_savings"],
                        annual_savings=r["annual_savings"],
                        priority=r["priority"],
                        status=r["status"],
                        difficulty=r["difficulty"],
                    )
                )
            return recs_objs

    def get_recommendation_summary(self, user_id: str) -> dict:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {
                "total_recommendations": 0,
                "total_monthly_savings": 0.0,
                "total_annual_savings": 0.0,
                "by_priority": {},
                "by_category": {},
                "by_status": {},
            }

        # 1. Reviewer Account (Demo Mode)
        if user.is_demo_mode:
            recs = (
                self.db.query(Recommendation)
                .filter(Recommendation.user_id == user_id)
                .all()
            )
        # 2. Normal User
        else:
            if not user.is_aws_connected:
                return {
                    "total_recommendations": 0,
                    "total_monthly_savings": 0.0,
                    "total_annual_savings": 0.0,
                    "by_priority": {},
                    "by_category": {},
                    "by_status": {},
                }
            aws_account = self.db.query(AWSAccount).filter(AWSAccount.org_id == user.org_id, AWSAccount.is_active.is_(True)).first()
            if not aws_account:
                return {
                    "total_recommendations": 0,
                    "total_monthly_savings": 0.0,
                    "total_annual_savings": 0.0,
                    "by_priority": {},
                    "by_category": {},
                    "by_status": {},
                }
            from app.services.aws_cost_explorer import cost_explorer_service
            raw_recs = cost_explorer_service.fetch_live_rightsizing_recommendations(aws_account)
            recs = [Recommendation(user_id=user_id, **r) for r in raw_recs]

        total_monthly = sum(
            r.monthly_savings for r in recs if r.status in ["pending", "accepted"]
        )
        total_annual = sum(
            r.annual_savings for r in recs if r.status in ["pending", "accepted"]
        )
        by_priority: dict[str, int] = {}
        by_category: dict[str, int] = {}
        by_status: dict[str, int] = {}
        for r in recs:
            by_priority[r.priority] = by_priority.get(r.priority, 0) + 1
            by_category[r.category or "other"] = (
                by_category.get(r.category or "other", 0) + 1
            )
            by_status[r.status] = by_status.get(r.status, 0) + 1

        return {
            "total_recommendations": len(recs),
            "total_monthly_savings": round(total_monthly, 2),
            "total_annual_savings": round(total_annual, 2),
            "by_priority": by_priority,
            "by_category": by_category,
            "by_status": by_status,
        }

    def update_status(self, rec_id: str, user_id: str, status: str) -> Recommendation:
        rec = self.rec_repo.get_by_id(rec_id)
        if not rec:
            from app.core.exceptions import EntityNotFoundError
            raise EntityNotFoundError("Recommendation", rec_id)
        if rec.user_id != user_id:
            from app.core.exceptions import AuthorizationError
            raise AuthorizationError(
                "You do not have permission to modify this recommendation"
            )
        return self.rec_repo.update(rec, {"status": status})

    def get_idle_resources(self, user_id: str) -> IdleResourceSummary:
        """Fetch identified idle / underutilized compute, database, and storage assets."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_demo_mode:
            # Normal users should not see fabricated idle resources
            return IdleResourceSummary(
                total_idle=0,
                total_savings=0.0,
                resources=[],
                by_type={},
            )

        idle_items = [
            IdleResource(
                resource_id="i-0a8b9c1d2e3f4g5h6",
                resource_type="EC2",
                resource_name="dev-worker-node-03",
                region="us-east-1",
                current_cost=122.64,
                estimated_savings=122.64,
                reason="Terminate idle development node or downscale to t3.micro (idle for 14 days)",
                details={"cpu_utilization_avg": "2.4%", "network_in_out": "12MB/day"},
                detected_at=datetime.utcnow() - timedelta(days=14),
            ),
            IdleResource(
                resource_id="vol-0123456789abcdef0",
                resource_type="EBS",
                resource_name="unattached-backup-vol",
                region="us-east-1",
                current_cost=40.00,
                estimated_savings=40.00,
                reason="Create snapshot and delete unattached EBS volume (idle for 28 days)",
                details={"iops": "0", "attached": False},
                detected_at=datetime.utcnow() - timedelta(days=28),
            ),
            IdleResource(
                resource_id="rds-staging-replica-01",
                resource_type="RDS",
                resource_name="staging-db-read-replica",
                region="us-west-2",
                current_cost=175.20,
                estimated_savings=175.20,
                reason="Pause or terminate unused staging database replica (idle for 21 days)",
                details={"connections_avg": "0", "read_iops": "0"},
                detected_at=datetime.utcnow() - timedelta(days=21),
            ),
        ]

        total_savings = sum(item.estimated_savings for item in idle_items)
        by_type = {
            "EC2": 1,
            "EBS": 1,
            "RDS": 1,
        }

        return IdleResourceSummary(
            total_idle=len(idle_items),
            total_savings=round(total_savings, 2),
            resources=idle_items,
            by_type=by_type,
        )

    def _generate_default_recommendations(self, user_id: str) -> None:
        """Generate baseline FinOps recommendations for user accounts."""
        defaults = [
            {
                "user_id": user_id,
                "service": "Amazon EC2",
                "resource_id": "i-09f1a2b3c4d5e6f7",
                "resource_type": "c5.2xlarge",
                "category": "rightsizing",
                "recommendation": "Rightsize CPU-underutilized c5.2xlarge to c5.large (Avg CPU 14%)",
                "current_cost": 244.80,
                "optimized_cost": 61.20,
                "monthly_savings": 183.60,
                "annual_savings": 2203.20,
                "priority": "high",
                "status": "pending",
                "difficulty": "easy",
            },
            {
                "user_id": user_id,
                "service": "Amazon RDS",
                "resource_id": "db-prod-replica-az2",
                "resource_type": "db.m5.2xlarge",
                "category": "purchasing_option",
                "recommendation": "Purchase 1-Year Reserved Instance for Production Multi-AZ RDS",
                "current_cost": 560.00,
                "optimized_cost": 364.00,
                "monthly_savings": 196.00,
                "annual_savings": 2352.00,
                "priority": "high",
                "status": "pending",
                "difficulty": "medium",
            },
            {
                "user_id": user_id,
                "service": "Amazon S3",
                "resource_id": "analytics-raw-logs-bucket",
                "resource_type": "S3 Standard",
                "category": "storage",
                "recommendation": "Enable S3 Intelligent-Tiering and Glacier Instant Retrieval transition rule (90+ days)",
                "current_cost": 320.00,
                "optimized_cost": 96.00,
                "monthly_savings": 224.00,
                "annual_savings": 2688.00,
                "priority": "medium",
                "status": "pending",
                "difficulty": "easy",
            },
        ]
        for d in defaults:
            rec = Recommendation(**d)
            self.db.add(rec)
        self.db.commit()
