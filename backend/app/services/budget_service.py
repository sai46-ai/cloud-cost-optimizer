"""
Budget Service
CRUD operations and alert management for budgets.
"""

from typing import List
from sqlalchemy.orm import Session

from app.models.budget import Budget
from app.repositories.budget_repository import BudgetRepository
from app.core.exceptions import EntityNotFoundError


class BudgetService:
    def __init__(self, db: Session):
        self.db = db
        self.budget_repo = BudgetRepository(db)

    def create_budget(self, user_id: str, data: dict) -> Budget:
        budget = Budget(user_id=user_id, **data)
        created = self.budget_repo.create(budget)
        created.spent = self._calculate_budget_spent(user_id, created)
        return created

    def get_budgets(self, user_id: str) -> List[Budget]:
        budgets = self.budget_repo.get_by_user(user_id)
        for b in budgets:
            b.spent = self._calculate_budget_spent(user_id, b)
        return budgets

    def get_budget(self, user_id: str, budget_id: str) -> Budget:
        budget = self.budget_repo.get_by_id(budget_id)
        if not budget or budget.user_id != user_id:
            raise EntityNotFoundError("Budget", budget_id)
        budget.spent = self._calculate_budget_spent(user_id, budget)
        return budget

    def update_budget(self, user_id: str, budget_id: str, data: dict) -> Budget:
        budget = self.get_budget(user_id, budget_id)
        updated = self.budget_repo.update(budget, data)
        updated.spent = self._calculate_budget_spent(user_id, updated)
        return updated

    def delete_budget(self, user_id: str, budget_id: str) -> None:
        budget = self.get_budget(user_id, budget_id)
        self.budget_repo.delete(budget)

    def _calculate_budget_spent(self, user_id: str, budget: Budget) -> float:
        from datetime import date, timedelta

        today = date.today()

        # Calculate start and end dates based on period
        if budget.period == "daily":
            start_date = today
            end_date = today
        elif budget.period == "weekly":
            start_date = today - timedelta(
                days=today.weekday()
            )  # Monday of the current week
            end_date = today
        else:  # monthly
            start_date = today.replace(day=1)
            end_date = today

        # Determine service filter from budget name heuristic
        name_lower = budget.name.lower()
        service_filter = None
        if "ec2" in name_lower:
            service_filter = "Amazon EC2"
        elif "rds" in name_lower or "db" in name_lower:
            service_filter = "Amazon RDS"
        elif "s3" in name_lower or "storage" in name_lower or "backup" in name_lower:
            service_filter = "Amazon S3"
        elif "lambda" in name_lower:
            service_filter = "AWS Lambda"
        elif "cloudfront" in name_lower:
            service_filter = "Amazon CloudFront"
        elif "dynamodb" in name_lower or "dynamo" in name_lower:
            service_filter = "Amazon DynamoDB"

        # Query cost records
        from app.models.cost_record import CostRecord
        from sqlalchemy import func

        query = self.db.query(func.sum(CostRecord.amount)).filter(
            CostRecord.user_id == user_id,
            CostRecord.date >= start_date,
            CostRecord.date <= end_date,
        )
        if service_filter:
            query = query.filter(CostRecord.service == service_filter)

        result = query.scalar()
        return round(result or 0.0, 2)
