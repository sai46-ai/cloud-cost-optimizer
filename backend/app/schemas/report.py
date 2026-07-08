"""Report schemas."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ReportCreateRequest(BaseModel):
    report_type: str = "cost_summary"  # cost_summary, optimization, anomaly
    format: str = "pdf"  # pdf, csv
    schedule: Optional[str] = None  # daily, weekly, monthly, None=on_demand


class ReportResponse(BaseModel):
    id: str
    report_type: str
    format: str
    filename: Optional[str] = None
    s3_key: Optional[str] = None
    file_size: Optional[float] = None
    schedule: Optional[str] = None
    status: str
    generated_at: datetime

    model_config = {"from_attributes": True}
