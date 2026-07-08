"""Recommendations & idle resources API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from typing import List
from app.database import get_db
from app.services.recommendation_service import RecommendationService
from app.schemas.recommendation import (
    RecommendationUpdateRequest,
    RecommendationResponse,
    RecommendationSummary,
    IdleResourceSummary,
)
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/", response_model=List[RecommendationResponse])
async def get_recommendations(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get all optimization recommendations."""
    service = RecommendationService(db)
    recs = await service.get_recommendations(user.id)
    return [
        {
            "id": r.id,
            "service": r.service,
            "resource_id": r.resource_id,
            "resource_type": r.resource_type,
            "category": r.category,
            "recommendation": r.recommendation,
            "current_cost": r.current_cost,
            "optimized_cost": r.optimized_cost,
            "monthly_savings": r.monthly_savings,
            "annual_savings": r.annual_savings,
            "priority": r.priority,
            "status": r.status,
            "difficulty": r.difficulty,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in recs
    ]


@router.get("/summary", response_model=RecommendationSummary)
def get_recommendation_summary(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """Get recommendation summary with totals."""
    service = RecommendationService(db)
    return service.get_recommendation_summary(user.id)


@router.get("/idle-resources", response_model=IdleResourceSummary)
def get_idle_resources(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """Get detected idle/underutilized AWS resources."""
    service = RecommendationService(db)
    return service.get_idle_resources(user.id)


@router.put("/{rec_id}/status", response_model=RecommendationResponse)
def update_recommendation_status(
    rec_id: str,
    data: RecommendationUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update recommendation status (accept/dismiss/implement)."""
    service = RecommendationService(db)
    rec = service.update_status(rec_id, user.id, data.status)
    return rec
