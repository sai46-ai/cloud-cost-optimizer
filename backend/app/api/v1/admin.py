"""
Admin API Router
Provides endpoints for user management, role assignments, system statistics, and audit trail queries.
Guarded strictly by require_admin.
"""
from datetime import datetime, timezone
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy import func, or_, desc, asc
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import require_admin
from app.models.user import User, UserRole
from app.models.audit_log import AuditLog
from app.models.aws_account import AWSAccount
from app.models.organization import Organization
from app.services.audit_service import AuditService
from app.schemas.auth import UserResponse

router = APIRouter()
logger = logging.getLogger("cloudwise")

# --- Schemas ---

class AdminDashboardStats(BaseModel):
    total_users: int
    total_reviewers: int
    aws_connected_users: int
    active_users: int
    demo_users: int
    system_status: str

class UserListResponse(BaseModel):
    items: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class UpdateRoleRequest(BaseModel):
    role: str

class UpdateStatusRequest(BaseModel):
    account_status: str

# --- Routes ---

@router.get("/dashboard", response_model=AdminDashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Retrieve system-wide KPIs for the Admin Dashboard."""
    total_users = db.query(User).count()
    total_reviewers = db.query(User).filter(User.role == UserRole.REVIEWER.value).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    demo_users = total_reviewers  # Reviewers are demo users

    # Calculate AWS connected users
    all_users = db.query(User).all()
    aws_connected_users = sum(1 for u in all_users if u.is_aws_connected)

    return AdminDashboardStats(
        total_users=total_users,
        total_reviewers=total_reviewers,
        aws_connected_users=aws_connected_users,
        active_users=active_users,
        demo_users=demo_users,
        system_status="operational"
    )

@router.get("/users", response_model=UserListResponse)
def list_users(
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    account_status: Optional[str] = Query(None),
    aws_connected: Optional[bool] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Retrieve users list with filtering, searching, sorting, and pagination."""
    query = db.query(User)

    # Search
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                User.full_name.ilike(search_filter),
                User.email.ilike(search_filter)
            )
        )

    # Filters
    if role:
        query = query.filter(User.role == role)
    if account_status:
        query = query.filter(User.account_status == account_status)

    # Sorting base
    sort_column = getattr(User, sort_by, User.created_at)
    if sort_order.lower() == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    # Load all items first to filter by python properties if needed
    users = query.all()

    # Filter by AWS Connected property (since organization is SELECTIN loaded, this is fast in memory)
    if aws_connected is not None:
        users = [u for u in users if u.is_aws_connected == aws_connected]

    total = len(users)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    
    # Paginate list
    start_idx = (page - 1) * page_size
    paginated_users = users[start_idx : start_idx + page_size]

    return UserListResponse(
        items=paginated_users,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.put("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    request: Request,
    user_id: str,
    data: UpdateRoleRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Assign or update a user's role. Prevents self-modification."""
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Privilege escalation guard: you cannot modify your own administrative role."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    new_role = data.role.upper()
    if new_role not in [UserRole.ADMIN.value, UserRole.REVIEWER.value, UserRole.USER.value]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid role '{new_role}'. Supported roles: ADMIN, REVIEWER, USER."
        )

    old_role = user.role
    user.role = new_role
    db.commit()
    db.refresh(user)

    # Audit log entry
    action_type = "user_role_changed"
    if new_role == UserRole.REVIEWER.value:
        action_type = "reviewer_assigned"
    elif old_role == UserRole.REVIEWER.value and new_role != UserRole.REVIEWER.value:
        action_type = "reviewer_removed"

    AuditService.log_action(
        db=db,
        user_id=admin.id,
        action=action_type,
        resource_type="user",
        resource_id=user.id,
        description=f"Admin updated role of {user.email} from {old_role} to {new_role}.",
        old_value={"role": old_role},
        new_value={"role": new_role},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return user

@router.put("/users/{user_id}/status", response_model=UserResponse)
def update_user_status(
    request: Request,
    user_id: str,
    data: UpdateStatusRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Enable or disable a user account. Prevents self-disablement."""
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Self-disablement guard: you cannot disable your own administrative account."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    new_status = data.account_status.lower()
    if new_status not in ["active", "disabled"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status '{new_status}'. Supported: active, disabled."
        )

    old_status = user.account_status
    user.account_status = new_status
    user.is_active = (new_status == "active")
    db.commit()
    db.refresh(user)

    action_type = "user_enabled" if new_status == "active" else "user_disabled"
    AuditService.log_action(
        db=db,
        user_id=admin.id,
        action=action_type,
        resource_type="user",
        resource_id=user.id,
        description=f"Admin set account status of {user.email} to {new_status}.",
        old_value={"account_status": old_status, "is_active": (old_status == "active")},
        new_value={"account_status": new_status, "is_active": user.is_active},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return user

@router.get("/audit-logs")
def list_admin_audit_logs(
    action: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Retrieve paginated list of all administrative audit logs for auditing/compliance."""
    query = db.query(AuditLog)
    
    # Filter for administrative actions
    admin_actions = [
        "reviewer_assigned", "reviewer_removed", "user_role_changed",
        "user_disabled", "user_enabled", "admin_login"
    ]
    
    if action:
        query = query.filter(AuditLog.action == action)
    else:
        query = query.filter(AuditLog.action.in_(admin_actions))

    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }
