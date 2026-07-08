"""Common schemas for pagination, responses, and shared types."""

from pydantic import BaseModel
from typing import TypeVar, Generic, Optional, List
from datetime import datetime

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class MessageResponse(BaseModel):
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    detail: str
    code: str = "ERROR"


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str
    environment: str
    database: str = "connected"
    timestamp: datetime


class DateRangeParams(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    granularity: str = "DAILY"  # DAILY, MONTHLY
