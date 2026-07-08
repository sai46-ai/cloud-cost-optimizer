"""Cost data schemas."""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


class CostRecordResponse(BaseModel):
    id: str
    date: date
    service: str
    region: Optional[str] = None
    amount: float
    usage_quantity: Optional[float] = None
    granularity: str = "DAILY"
    ingested_at: datetime

    model_config = {"from_attributes": True}


class CostSummary(BaseModel):
    total_cost: float
    previous_period_cost: float
    change_pct: float
    daily_average: float
    top_services: List["ServiceCost"]
    top_regions: List["RegionCost"]
    period: str


class ServiceCost(BaseModel):
    service: str
    amount: float
    percentage: float
    trend: str = "stable"  # up, down, stable


class RegionCost(BaseModel):
    region: str
    amount: float
    percentage: float


class CostTrend(BaseModel):
    date: str
    amount: float
    service: Optional[str] = None


class DashboardMetrics(BaseModel):
    total_spend_mtd: float
    total_spend_prev_month: float
    spend_change_pct: float
    daily_spend_avg: float
    forecasted_month_end: float
    total_savings_opportunity: float
    active_anomalies: int
    budget_health_pct: float
    top_services: List[ServiceCost]
    top_regions: List[RegionCost]
    daily_costs: List[CostTrend]
    monthly_costs: List[CostTrend]


class CostBreakdown(BaseModel):
    by_service: List[ServiceCost]
    by_region: List[RegionCost]
    daily_trend: List[CostTrend]
    total: float
