"""Forecast API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.ai.forecaster import CostForecaster
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.forecast import ForecastSummary

router = APIRouter()


@router.get("/", response_model=ForecastSummary)
def get_forecasts(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """Get latest cost forecasts for all horizons."""
    forecaster = CostForecaster(db)
    return forecaster.get_latest_forecasts(user.id)


@router.post("/generate")
def generate_forecasts(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """Trigger forecast generation."""
    forecaster = CostForecaster(db)
    forecasts = forecaster.generate_forecasts(user.id)
    return {
        "message": f"Generated {len(forecasts)} forecasts",
        "forecasts": [
            {
                "horizon": f.horizon,
                "predicted_amount": f.predicted_amount,
                "lower_bound": f.lower_bound,
                "upper_bound": f.upper_bound,
            }
            for f in forecasts
        ],
    }
