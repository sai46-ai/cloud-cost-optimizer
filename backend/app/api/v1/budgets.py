"""Budget API routes — full CRUD."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.services.budget_service import BudgetService
from app.services.audit_service import AuditService
from app.schemas.budget import BudgetCreateRequest, BudgetUpdateRequest, BudgetResponse
from app.api.deps import get_current_user, require_manager
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[BudgetResponse])
def get_budgets(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get all budgets for the current user."""
    service = BudgetService(db)
    return service.get_budgets(user.id)


@router.post(
    "/", response_model=BudgetResponse, dependencies=[Depends(require_manager)]
)
def create_budget(
    request: Request,
    data: BudgetCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new budget."""
    service = BudgetService(db)
    result = service.create_budget(user.id, data.model_dump())
    AuditService.log_action(
        db=db,
        user_id=user.id,
        action="create",
        resource_type="budget",
        resource_id=result.id,
        description=f"Created budget: {result.name} (Limit: ${result.amount:,.2f})",
        new_value=data.model_dump(),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return result


@router.get("/{budget_id}", response_model=BudgetResponse)
def get_budget(
    budget_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a specific budget by ID."""
    service = BudgetService(db)
    return service.get_budget(user.id, budget_id)


@router.put(
    "/{budget_id}",
    response_model=BudgetResponse,
    dependencies=[Depends(require_manager)],
)
def update_budget(
    request: Request,
    budget_id: str,
    data: BudgetUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update a budget."""
    service = BudgetService(db)
    old_budget = service.get_budget(user.id, budget_id)
    old_val = {
        "name": old_budget.name,
        "amount": old_budget.amount,
        "period": old_budget.period,
        "alert_threshold_50": old_budget.alert_threshold_50,
        "alert_threshold_80": old_budget.alert_threshold_80,
        "alert_threshold_90": old_budget.alert_threshold_90,
        "alert_threshold_100": old_budget.alert_threshold_100,
    }
    result = service.update_budget(
        user.id, budget_id, data.model_dump(exclude_unset=True)
    )
    AuditService.log_action(
        db=db,
        user_id=user.id,
        action="update",
        resource_type="budget",
        resource_id=budget_id,
        description=f"Updated budget: {result.name}",
        old_value=old_val,
        new_value=data.model_dump(exclude_unset=True),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return result


@router.delete("/{budget_id}", dependencies=[Depends(require_manager)])
def delete_budget(
    request: Request,
    budget_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a budget."""
    service = BudgetService(db)
    budget = service.get_budget(user.id, budget_id)
    budget_name = budget.name
    service.delete_budget(user.id, budget_id)
    AuditService.log_action(
        db=db,
        user_id=user.id,
        action="delete",
        resource_type="budget",
        resource_id=budget_id,
        description=f"Deleted budget: {budget_name}",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return {"message": "Budget deleted successfully"}

