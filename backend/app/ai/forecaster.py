"""
Cost Forecaster
Time-series forecasting for AWS cost prediction.
Uses statistical methods with fallback when Prophet is not available.
"""

import logging
from datetime import date, timedelta, datetime, timezone
from typing import List

try:
    import numpy as np
    import pandas as pd

    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
from sqlalchemy.orm import Session

from app.models.cost_record import CostRecord, DemoCostRecord, AWSCostRecord
from app.models.forecast import Forecast, DemoForecast, AWSForecast
from app.models.user import User
from app.models.aws_account import AWSAccount

logger = logging.getLogger(__name__)


class CostForecaster:
    """Predicts future AWS costs using time-series analysis."""

    def __init__(self, db: Session):
        self.db = db

    def generate_forecasts(self, user_id: str) -> List[Any]:
        """Generate forecasts for multiple time horizons."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []

        # Get records based on user type
        if user.is_demo_mode:
            records = (
                self.db.query(DemoCostRecord)
                .filter(DemoCostRecord.user_id == user_id)
                .order_by(DemoCostRecord.date)
                .all()
            )
            forecast_cls = DemoForecast
        else:
            if not user.is_aws_connected:
                return []
            aws_account = self.db.query(AWSAccount).filter(AWSAccount.org_id == user.org_id, AWSAccount.is_active.is_(True)).first()
            if not aws_account:
                return []
            
            today = date.today()
            start_date = today - timedelta(days=90)
            from app.services.aws_cost_explorer import cost_explorer_service
            try:
                records = cost_explorer_service.get_live_costs(aws_account, start_date, today)
            except Exception as e:
                logger.warning("Failed to fetch live costs for forecasting: %s. Falling back to local AWS records.", e)
                records = (
                    self.db.query(AWSCostRecord)
                    .filter(AWSCostRecord.user_id == user_id)
                    .order_by(AWSCostRecord.date)
                    .all()
                )
            forecast_cls = AWSForecast

        if not ML_AVAILABLE or len(records) < 14:
            logger.warning(
                "Insufficient data or ML missing for forecasting (need 14+ daily records)"
            )
            return []

        # Aggregate daily totals
        df = pd.DataFrame([
            {
                "date": r.date if not isinstance(r, dict) else r.get("date"),
                "amount": r.amount if not isinstance(r, dict) else r.get("amount")
            } 
            for r in records
        ])
        df["date"] = pd.to_datetime(df["date"])
        daily = df.groupby("date")["amount"].sum().reset_index()
        daily = daily.sort_values("date")

        forecasts = []
        for horizon, days_ahead, label in [
            ("day", 1, "Next Day"),
            ("week", 7, "Next Week"),
            ("month", 30, "Next Month"),
            ("quarter", 90, "Next Quarter"),
        ]:
            pred, lower, upper = self._forecast_statistical(daily, days_ahead)
            forecast = forecast_cls(
                user_id=user_id,
                horizon=horizon,
                forecast_date=date.today() + timedelta(days=days_ahead),
                predicted_amount=round(pred, 2),
                lower_bound=round(lower, 2),
                upper_bound=round(upper, 2),
                confidence=0.95,
                model_used="statistical_ensemble",
                trend_data=self._build_trend_data(daily, days_ahead),
                generated_at=datetime.now(timezone.utc),
            )
            forecasts.append(forecast)
            
            # Save to database only for reviewers
            if user.is_demo_mode:
                self.db.add(forecast)

        if user.is_demo_mode:
            self.db.commit()
            
        return forecasts

    def get_latest_forecasts(self, user_id: str) -> dict:
        """Get the most recent forecast for each horizon."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}

        if user.is_demo_mode:
            horizons = ["day", "week", "month", "quarter"]
            result = {}
            for h in horizons:
                forecast = (
                    self.db.query(DemoForecast)
                    .filter(DemoForecast.user_id == user_id, DemoForecast.horizon == h)
                    .order_by(DemoForecast.generated_at.desc())
                    .first()
                )
                if forecast:
                    result[f"next_{h}"] = {
                        "id": forecast.id,
                        "horizon": forecast.horizon,
                        "forecast_date": str(forecast.forecast_date),
                        "predicted_amount": forecast.predicted_amount,
                        "lower_bound": forecast.lower_bound,
                        "upper_bound": forecast.upper_bound,
                        "confidence": forecast.confidence,
                        "model_used": forecast.model_used,
                        "generated_at": (
                            forecast.generated_at.isoformat()
                            if forecast.generated_at
                            else None
                        ),
                    }
            return result
        else:
            # Generate dynamically on the fly
            forecasts = self.generate_forecasts(user_id)
            result = {}
            for forecast in forecasts:
                result[f"next_{forecast.horizon}"] = {
                    "id": getattr(forecast, "id", f"live-forecast-{forecast.horizon}"),
                    "horizon": forecast.horizon,
                    "forecast_date": str(forecast.forecast_date),
                    "predicted_amount": forecast.predicted_amount,
                    "lower_bound": forecast.lower_bound,
                    "upper_bound": forecast.upper_bound,
                    "confidence": forecast.confidence,
                    "model_used": forecast.model_used,
                    "generated_at": (
                        forecast.generated_at.isoformat()
                        if forecast.generated_at
                        else None
                    ),
                }
            return result

    def _forecast_statistical(self, daily: pd.DataFrame, days_ahead: int) -> tuple:
        """Statistical forecasting using weighted moving average + trend."""
        amounts = daily["amount"].values
        n = len(amounts)

        if n < 7:
            mean_val = np.mean(amounts)
            return (
                mean_val * days_ahead,
                mean_val * days_ahead * 0.8,
                mean_val * days_ahead * 1.2,
            )

        # Weighted moving average (recent days weighted more)
        weights = np.exp(np.linspace(-1, 0, min(30, n)))
        weights /= weights.sum()
        recent = amounts[-min(30, n) :]
        wma = np.average(recent, weights=weights[-len(recent) :])

        # Trend: linear regression on last 30 days
        x = np.arange(len(recent))
        coeffs = np.polyfit(x, recent, 1)
        daily_trend = coeffs[0]

        # Predict
        prediction = (wma + daily_trend * days_ahead) * days_ahead
        std_dev = np.std(recent) * np.sqrt(days_ahead)

        lower = max(0, prediction - 1.96 * std_dev)
        upper = prediction + 1.96 * std_dev

        return max(0, prediction), lower, upper

    def _build_trend_data(self, daily: pd.DataFrame, forecast_days: int) -> list:
        """Build trend data including historical + predicted values."""
        recent = daily.tail(30)
        trend = []
        for _, row in recent.iterrows():
            trend.append(
                {
                    "date": str(row["date"].date()),
                    "amount": round(row["amount"], 2),
                    "type": "actual",
                }
            )

        # Add forecast points
        last_amount = recent["amount"].iloc[-1] if len(recent) > 0 else 0
        daily_change = (recent["amount"].diff().mean()) if len(recent) > 1 else 0

        for i in range(1, min(forecast_days + 1, 31)):
            trend.append(
                {
                    "date": str(date.today() + timedelta(days=i)),
                    "amount": round(max(0, last_amount + daily_change * i), 2),
                    "type": "forecast",
                }
            )

        return trend
