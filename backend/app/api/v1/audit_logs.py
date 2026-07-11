"""
Audit Log API routes
Lists security and administrative audit trail logs for enterprise governance.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.audit_log import AuditLog

router = APIRouter()


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    description: Optional[str]
    ip_address: Optional[str]
    created_at: datetime


class AuditLogListResponse(BaseModel):
    items: List[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.get("/", response_model=AuditLogListResponse)
def get_audit_logs(
    action: Optional[str] = Query(
        None, description="Filter by action type (e.g. login, register, create, update)"
    ),
    resource_type: Optional[str] = Query(
        None, description="Filter by resource type (e.g. budget, report, settings)"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List audit log events for the authenticated user's organization."""
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)

    total = query.count()
    offset = (page - 1) * page_size
    items = (
        query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size).all()
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return AuditLogListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
