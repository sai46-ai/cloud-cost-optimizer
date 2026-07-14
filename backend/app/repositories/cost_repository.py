"""Cost Record repository with specialized query methods."""

from typing import List, Optional
from datetime import date, timedelta
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.models.cost_record import CostRecord, DemoCostRecord, AWSCostRecord
from app.repositories.base import BaseRepository


class CostRepository(BaseRepository[CostRecord]):
    def __init__(self, db: Session):
        super().__init__(CostRecord, db)

    def get_by_date_range(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
        service: Optional[str] = None,
        is_demo: bool = True,
    ) -> List[CostRecord]:
        model = DemoCostRecord if is_demo else AWSCostRecord
        query = self.db.query(model).filter(
            model.user_id == user_id,
            model.date >= start_date,
            model.date <= end_date,
        )
        if service:
            query = query.filter(model.service == service)
        return query.order_by(model.date).all()

    def get_total_by_date_range(
        self, user_id: str, start_date: date, end_date: date, is_demo: bool = True
    ) -> float:
        model = DemoCostRecord if is_demo else AWSCostRecord
        result = (
            self.db.query(func.sum(model.amount))
            .filter(
                model.user_id == user_id,
                model.date >= start_date,
                model.date <= end_date,
            )
            .scalar()
        )
        return result or 0.0

    def get_daily_totals(
        self, user_id: str, start_date: date, end_date: date, is_demo: bool = True
    ) -> List[dict]:
        model = DemoCostRecord if is_demo else AWSCostRecord
        results = (
            self.db.query(model.date, func.sum(model.amount).label("total"))
            .filter(
                model.user_id == user_id,
                model.date >= start_date,
                model.date <= end_date,
            )
            .group_by(model.date)
            .order_by(model.date)
            .all()
        )
        return [{"date": str(r.date), "amount": round(r.total, 2)} for r in results]

    def get_top_services(
        self, user_id: str, start_date: date, end_date: date, limit: int = 10, is_demo: bool = True
    ) -> List[dict]:
        model = DemoCostRecord if is_demo else AWSCostRecord
        results = (
            self.db.query(
                model.service,
                func.sum(model.amount).label("total"),
            )
            .filter(
                model.user_id == user_id,
                model.date >= start_date,
                model.date <= end_date,
            )
            .group_by(model.service)
            .order_by(desc("total"))
            .limit(limit)
            .all()
        )
        grand_total = sum(r.total for r in results) or 1.0
        return [
            {
                "service": r.service,
                "amount": round(r.total, 2),
                "percentage": round((r.total / grand_total) * 100, 1),
            }
            for r in results
        ]

    def get_top_regions(
        self, user_id: str, start_date: date, end_date: date, limit: int = 10, is_demo: bool = True
    ) -> List[dict]:
        model = DemoCostRecord if is_demo else AWSCostRecord
        results = (
            self.db.query(
                model.region,
                func.sum(model.amount).label("total"),
            )
            .filter(
                model.user_id == user_id,
                model.date >= start_date,
                model.date <= end_date,
            )
            .group_by(model.region)
            .order_by(desc("total"))
            .limit(limit)
            .all()
        )
        grand_total = sum(r.total for r in results) or 1.0
        return [
            {
                "region": r.region or "us-east-1",
                "amount": round(r.total, 2),
                "percentage": round((r.total / grand_total) * 100, 1),
            }
            for r in results
        ]

    def get_monthly_totals(self, user_id: str, months: int = 12, is_demo: bool = True) -> List[dict]:
        """Get monthly cost totals for the last N months (database-agnostic).

        Uses full-model query + Python-side grouping instead of func.strftime,
        which is SQLite-only and breaks on MongoDB.
        """
        model = DemoCostRecord if is_demo else AWSCostRecord
        end = date.today()
        start = end - timedelta(days=months * 31)
        # Query full objects — works correctly with both SQLite and MongoDB shim
        results = (
            self.db.query(model)
            .filter(model.user_id == user_id, model.date >= start)
            .all()
        )
        # Group by YYYY-MM in Python
        monthly: dict = {}
        for r in results:
            d = getattr(r, "date", None)
            amt = getattr(r, "amount", 0.0) or 0.0
            if d is None:
                continue
            key = d.strftime("%Y-%m") if hasattr(d, "strftime") else str(d)[:7]
            monthly[key] = round(monthly.get(key, 0.0) + amt, 2)
        return [{"date": k, "amount": v} for k, v in sorted(monthly.items())]
