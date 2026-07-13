from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone

from app.database import get_db
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/liveness")
def liveness_check():
    """Liveness probe for K8s - returns 200 if app is running."""
    return {"status": "alive"}


@router.get("/readiness")
def readiness_check(response: Response, db: Session = Depends(get_db)):
    """Readiness probe for K8s - checks DB connection."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready", "reason": "Database connection failed"}


@router.get("/health")
def health_check(response: Response, db: Session = Depends(get_db)):
    """Detailed health check endpoint."""
    db_status = "connected"
    is_healthy = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"
        is_healthy = False
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger("cloudwise")


class FrontendLogRequest(BaseModel):
    level: str
    message: str
    component: Optional[str] = None
    stack: Optional[str] = None


@router.post("/logs/frontend", status_code=status.HTTP_200_OK)
def log_frontend_event(log: FrontendLogRequest):
    """Receive and log frontend exceptions/console events to central logs."""
    extra = {
        "component": log.component or "unknown",
        "stack": log.stack or "none"
    }
    log_msg = f"[FRONTEND] {log.message}"
    if log.level.lower() == "error":
        logger.error(log_msg, extra=extra)
    elif log.level.lower() == "warning" or log.level.lower() == "warn":
        logger.warning(log_msg, extra=extra)
    else:
        logger.info(log_msg, extra=extra)
    return {"status": "logged"}
