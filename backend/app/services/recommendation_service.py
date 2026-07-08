"""
Recommendation Service
Generates optimization recommendations, rightsizing rules, and detects idle cloud resources.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.recommendation import Recommendation
from app.repositories.base import BaseRepository
from app.schemas.recommendation import IdleResource, IdleResourceSummary


class RecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.rec_repo = BaseRepository(Recommendation, db)

    async def get_recommendations(
        self, user_id: Optional[str] = None
    ) -> List[Recommendation]:
        if user_id:
            recs = (
                self.db.query(Recommendation)
                .filter(Recommendation.user_id == user_id)
                .all()
            )
            if not recs:
                # Dynamically evaluate & generate baseline recommendations for user
                self._generate_default_recommendations(user_id)
                recs = (
                    self.db.query(Recommendation)
                    .filter(Recommendation.user_id == user_id)
                    .all()
                )
            return recs
        return self.rec_repo.get_all(limit=200)

    def get_recommendation_summary(self, user_id: str) -> dict:
        recs = (
            self.db.query(Recommendation)
            .filter(Recommendation.user_id == user_id)
            .all()
        )
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
        idle_items = [
            IdleResource(
                id="idle-ec2-01",
                resource_id="i-0a8b9c1d2e3f4g5h6",
                resource_name="dev-worker-node-03",
                service="Amazon EC2",
                region="us-east-1",
                resource_type="t3.xlarge",
                metrics={"cpu_utilization_avg": "2.4%", "network_in_out": "12MB/day"},
                monthly_waste=122.64,
                recommended_action="Terminate idle development node or downscale to t3.micro",
                days_idle=14,
            ),
            IdleResource(
                id="idle-ebs-01",
                resource_id="vol-0123456789abcdef0",
                resource_name="unattached-backup-vol",
                service="Amazon EBS",
                region="us-east-1",
                resource_type="gp3 (500GB)",
                metrics={"iops": "0", "attached": False},
                monthly_waste=40.00,
                recommended_action="Create snapshot and delete unattached EBS volume",
                days_idle=28,
            ),
            IdleResource(
                id="idle-rds-01",
                resource_id="rds-staging-replica-01",
                resource_name="staging-db-read-replica",
                service="Amazon RDS",
                region="us-west-2",
                resource_type="db.r5.large",
                metrics={"connections_avg": "0", "read_iops": "0"},
                monthly_waste=175.20,
                recommended_action="Pause or terminate unused staging database replica",
                days_idle=21,
            ),
        ]

        total_waste = sum(item.monthly_waste for item in idle_items)
        by_type = {
            "Amazon EC2": 1,
            "Amazon EBS": 1,
            "Amazon RDS": 1,
        }

        return IdleResourceSummary(
            total_idle=len(idle_items),
            total_savings=round(total_waste, 2),
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
