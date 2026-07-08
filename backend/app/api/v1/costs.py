"""Cost API routes — dashboard metrics, cost data, breakdowns."""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date

from app.database import get_db
from app.services.cost_service import CostService
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.cost import DashboardMetrics, CostBreakdown, CostRecordResponse

router = APIRouter()



def _parse_date(val: Optional[str]) -> Optional[date]:
    if not val:
        return None
    try:
        return date.fromisoformat(val)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid date format '{val}'. Expected YYYY-MM-DD.",
        )


@router.get("/dashboard", response_model=DashboardMetrics)
def get_dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get executive dashboard metrics."""
    service = CostService(db)
    return service.get_dashboard_metrics(user.id)


@router.get("/breakdown", response_model=CostBreakdown)
def get_cost_breakdown(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get cost breakdown by service and region."""
    service = CostService(db)
    sd = _parse_date(start_date)
    ed = _parse_date(end_date)
    return service.get_cost_breakdown(user.id, sd, ed)


@router.get("/", response_model=List[CostRecordResponse])
def get_costs(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    service_name: Optional[str] = Query(None, alias="service"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get raw cost records with optional filtering."""
    cost_service = CostService(db)
    sd = _parse_date(start_date)
    ed = _parse_date(end_date)
    return cost_service.get_costs(user.id, sd, ed, service_name)
