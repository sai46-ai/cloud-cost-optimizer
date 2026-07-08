"""Recommendation schemas."""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class RecommendationResponse(BaseModel):
    id: str
    service: str
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    category: Optional[str] = None
    recommendation: str
    current_cost: float
    optimized_cost: float
    monthly_savings: float
    annual_savings: float
    priority: str
    status: str
    difficulty: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RecommendationUpdateRequest(BaseModel):
    status: str  # pending, accepted, dismissed, implemented


class RecommendationSummary(BaseModel):
    total_recommendations: int
    total_monthly_savings: float
    total_annual_savings: float
    by_priority: dict  # {"critical": 5, "high": 10, ...}
    by_category: dict  # {"rightsizing": 3, "reserved": 5, ...}
    by_status: dict


class IdleResource(BaseModel):
    resource_id: str
    resource_type: str  # EC2, RDS, EBS, EIP, ELB
    resource_name: Optional[str] = None
    region: str
    current_cost: float
    estimated_savings: float
    reason: str
    details: Optional[dict] = None
    detected_at: datetime


class IdleResourceSummary(BaseModel):
    total_idle: int
    total_savings: float
    resources: List[IdleResource]
    by_type: dict  # {"EC2": 3, "RDS": 2, ...}
