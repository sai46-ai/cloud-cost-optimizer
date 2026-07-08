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
