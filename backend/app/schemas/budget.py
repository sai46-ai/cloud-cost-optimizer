"""Budget schemas."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class BudgetCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    amount: float = Field(gt=0)
    period: str = "monthly"
    alert_threshold_50: bool = True
    alert_threshold_80: bool = True
    alert_threshold_90: bool = True
    alert_threshold_100: bool = True
    email_enabled: bool = True
    sns_enabled: bool = False
    dashboard_enabled: bool = True


class BudgetUpdateRequest(BaseModel):
    name: Optional[str] = None
    amount: Optional[float] = Field(default=None, gt=0)
    period: Optional[str] = None
    alert_threshold_50: Optional[bool] = None
    alert_threshold_80: Optional[bool] = None
    alert_threshold_90: Optional[bool] = None
    alert_threshold_100: Optional[bool] = None
    email_enabled: Optional[bool] = None
    sns_enabled: Optional[bool] = None
    dashboard_enabled: Optional[bool] = None
    is_active: Optional[bool] = None


class BudgetResponse(BaseModel):
    id: str
    name: str
    amount: float
    period: str
    spent: float
    utilization_pct: float
    status: str
    alert_threshold_50: bool
    alert_threshold_80: bool
    alert_threshold_90: bool
    alert_threshold_100: bool
    email_enabled: bool
    sns_enabled: bool
    dashboard_enabled: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
