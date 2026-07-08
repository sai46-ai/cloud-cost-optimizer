"""Cost Record repository with specialized query methods."""

from typing import List, Optional
from datetime import date, timedelta
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.models.cost_record import CostRecord
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
    ) -> List[CostRecord]:
        query = self.db.query(CostRecord).filter(
            CostRecord.user_id == user_id,
            CostRecord.date >= start_date,
            CostRecord.date <= end_date,
        )
        if service:
            query = query.filter(CostRecord.service == service)
        return query.order_by(CostRecord.date).all()

    def get_total_by_date_range(
        self, user_id: str, start_date: date, end_date: date
    ) -> float:
        result = (
            self.db.query(func.sum(CostRecord.amount))
            .filter(
                CostRecord.user_id == user_id,
                CostRecord.date >= start_date,
                CostRecord.date <= end_date,
            )
            .scalar()
        )
        return result or 0.0

    def get_daily_totals(
        self, user_id: str, start_date: date, end_date: date
    ) -> List[dict]:
        results = (
            self.db.query(CostRecord.date, func.sum(CostRecord.amount).label("total"))
            .filter(
                CostRecord.user_id == user_id,
                CostRecord.date >= start_date,
                CostRecord.date <= end_date,
            )
            .group_by(CostRecord.date)
            .order_by(CostRecord.date)
            .all()
        )
        return [{"date": str(r.date), "amount": round(r.total, 2)} for r in results]

    def get_top_services(
        self, user_id: str, start_date: date, end_date: date, limit: int = 10
    ) -> List[dict]:
        results = (
            self.db.query(
                CostRecord.service,
                func.sum(CostRecord.amount).label("total"),
            )
            .filter(
                CostRecord.user_id == user_id,
                CostRecord.date >= start_date,
                CostRecord.date <= end_date,
            )
            .group_by(CostRecord.service)
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
        self, user_id: str, start_date: date, end_date: date, limit: int = 10
    ) -> List[dict]:
        results = (
            self.db.query(
                CostRecord.region,
                func.sum(CostRecord.amount).label("total"),
            )
            .filter(
                CostRecord.user_id == user_id,
                CostRecord.date >= start_date,
                CostRecord.date <= end_date,
            )
            .group_by(CostRecord.region)
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

    def get_monthly_totals(self, user_id: str, months: int = 12) -> List[dict]:
        """Get monthly cost totals for the last N months."""
        end = date.today()
        start = end - timedelta(days=months * 31)
        results = (
            self.db.query(
                func.strftime("%Y-%m", CostRecord.date).label("month"),
                func.sum(CostRecord.amount).label("total"),
            )
            .filter(CostRecord.user_id == user_id, CostRecord.date >= start)
            .group_by("month")
            .order_by("month")
            .all()
        )
        return [{"date": r.month, "amount": round(r.total, 2)} for r in results]
