"""Budget repository."""

from typing import List

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
from app.models.budget import Budget
from app.repositories.base import BaseRepository


class BudgetRepository(BaseRepository[Budget]):
    def __init__(self, db: Session):
        super().__init__(Budget, db)

    def get_by_user(self, user_id: str) -> List[Budget]:
        return self.db.query(Budget).filter(Budget.user_id == user_id).all()

    def get_active_by_user(self, user_id: str) -> List[Budget]:
        return (
            self.db.query(Budget)
            .filter(Budget.user_id == user_id, Budget.is_active.is_(True))
            .all()
        )
