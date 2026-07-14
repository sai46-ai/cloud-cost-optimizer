from typing import List, Any
from sqlalchemy.orm import Session

from app.models.budget import Budget, DemoBudget, AWSBudget
from app.models.user import User
from app.models.aws_account import AWSAccount
from app.core.exceptions import EntityNotFoundError


class BudgetService:
    def __init__(self, db: Session):
        self.db = db

    def create_budget(self, user_id: str, data: dict) -> Any:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise EntityNotFoundError("User", user_id)
        model = DemoBudget if user.is_demo_mode else AWSBudget
        budget = model(user_id=user_id, **data)
        self.db.add(budget)
        self.db.commit()
        self.db.refresh(budget)
        budget.spent = self._calculate_budget_spent(user_id, budget, user.is_demo_mode)
        return budget

    def get_budgets(self, user_id: str) -> List[Any]:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        model = DemoBudget if user.is_demo_mode else AWSBudget
        budgets = self.db.query(model).filter(model.user_id == user_id).all()
        for b in budgets:
            b.spent = self._calculate_budget_spent(user_id, b, user.is_demo_mode)
        return budgets

    def get_budget(self, user_id: str, budget_id: str) -> Any:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise EntityNotFoundError("User", user_id)
        model = DemoBudget if user.is_demo_mode else AWSBudget
        budget = self.db.query(model).filter(model.id == budget_id).first()
        if not budget or budget.user_id != user_id:
            raise EntityNotFoundError("Budget", budget_id)
        budget.spent = self._calculate_budget_spent(user_id, budget, user.is_demo_mode)
        return budget

    def update_budget(self, user_id: str, budget_id: str, data: dict) -> Any:
        budget = self.get_budget(user_id, budget_id)
        for key, value in data.items():
            if value is not None and hasattr(budget, key):
                setattr(budget, key, value)
        self.db.commit()
        self.db.refresh(budget)
        user = self.db.query(User).filter(User.id == user_id).first()
        budget.spent = self._calculate_budget_spent(user_id, budget, user.is_demo_mode)
        return budget

    def delete_budget(self, user_id: str, budget_id: str) -> None:
        budget = self.get_budget(user_id, budget_id)
        self.db.delete(budget)
        self.db.commit()

    def _calculate_budget_spent(self, user_id: str, budget: Any, is_demo: bool) -> float:
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

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return 0.0

        # If user is in demo mode, query the DB cost records
        if is_demo:
            from app.models.cost_record import DemoCostRecord
            from sqlalchemy import func

            query = self.db.query(func.sum(DemoCostRecord.amount)).filter(
                DemoCostRecord.user_id == user_id,
                DemoCostRecord.date >= start_date,
                DemoCostRecord.date <= end_date,
            )
            if service_filter:
                query = query.filter(DemoCostRecord.service == service_filter)

            result = query.scalar()
            return round(result or 0.0, 2)

        # For normal users, fetch live spend from AWS CE
        else:
            if not user.is_aws_connected:
                return 0.0

            aws_account = self.db.query(AWSAccount).filter(AWSAccount.org_id == user.org_id, AWSAccount.is_active.is_(True)).first()
            if not aws_account:
                return 0.0

            from app.services.aws_cost_explorer import cost_explorer_service
            try:
                return cost_explorer_service.get_live_spent(aws_account, start_date, end_date, service_filter)
            except Exception:
                # If query fails, let's return 0.0
                return 0.0
