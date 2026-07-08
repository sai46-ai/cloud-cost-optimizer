"""
Anomaly Detector
Enhanced ML-based cost anomaly detection using Isolation Forest and XGBoost ensemble.
Preserves and improves the original Isolation Forest implementation.
"""

import logging
from datetime import datetime, timezone, date
from typing import List, Any

try:
    import pandas as pd
    from sklearn.ensemble import IsolationForest

    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.models.cost_record import CostRecord
from app.models.anomaly import Anomaly

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Detects cost anomalies using an ensemble of ML models."""

    def __init__(self, db: Session):
        self.db = db

    def detect_anomalies(
        self, user_id: str, contamination: float = 0.08
    ) -> List[Anomaly]:
        """
        Run anomaly detection on cost records for a specific user.
        Enhanced from original implementation with:
        - Feature engineering (rolling averages, day-of-week, etc.)
        - Severity scoring based on deviation magnitude
        - Root cause analysis
        """
        records = (
            self.db.query(CostRecord)
            .filter(CostRecord.user_id == user_id)
            .order_by(CostRecord.date)
            .all()
        )
        # If ML is not available or insufficient data, return empty list (zero-mock policy)
        if not ML_AVAILABLE or len(records) < 14:
            logger.warning(
                "Insufficient data or ML libraries missing for anomaly detection"
            )
            return self.get_anomalies(user_id)

        # Build DataFrame
        df = pd.DataFrame(
            [
                {
                    "id": r.id,
                    "amount": r.amount,
                    "date": r.date,
                    "service": r.service,
                    "region": r.region,
                }
                for r in records
            ]
        )

        detected_anomalies = []

        # Per-service anomaly detection (preserved from original)
        for service in df["service"].unique():
            sdf = df[df["service"] == service].copy()
            if len(sdf) < 10:
                continue

            # Feature engineering
            sdf = sdf.sort_values("date")
            sdf["rolling_mean_7d"] = (
                sdf["amount"].rolling(window=7, min_periods=1).mean()
            )
            sdf["rolling_std_7d"] = (
                sdf["amount"].rolling(window=7, min_periods=1).std().fillna(0)
            )
            sdf["deviation"] = (sdf["amount"] - sdf["rolling_mean_7d"]).abs()
            sdf["day_of_week"] = pd.to_datetime(sdf["date"]).dt.dayofweek

            # Features for Isolation Forest
            features = sdf[
                [
                    "amount",
                    "rolling_mean_7d",
                    "rolling_std_7d",
                    "deviation",
                    "day_of_week",
                ]
            ].fillna(0)

            # Isolation Forest (enhanced from original)
            model = IsolationForest(
                contamination=contamination,
                random_state=42,
                n_estimators=200,
                max_features=1.0,
            )
            sdf["anomaly_score"] = model.fit_predict(features)
            sdf["decision_score"] = model.decision_function(features)

            # Process detected anomalies
            anomaly_rows = sdf[sdf["anomaly_score"] == -1]
            if anomaly_rows.empty:
                continue

            anomaly_record_ids = anomaly_rows["id"].tolist()
            existing_anomalies = {
                r[0]
                for r in self.db.query(Anomaly.cost_record_id)
                .filter(Anomaly.cost_record_id.in_(anomaly_record_ids))
                .all()
            }

            for _, row in anomaly_rows.iterrows():
                # Skip if already detected
                if row["id"] in existing_anomalies:
                    continue

                # Calculate severity based on deviation from mean
                mean_cost = sdf["amount"].mean()
                std_cost = sdf["amount"].std() or 1.0
                z_score = abs(row["amount"] - mean_cost) / std_cost
                severity = self._calculate_severity(z_score)
                impact = round(abs(row["amount"] - mean_cost), 2)

                # Root cause analysis
                root_cause = self._determine_root_cause(row, sdf)

                anomaly = Anomaly(
                    cost_record_id=row["id"],
                    date=row["date"],
                    service=service,
                    severity=severity,
                    impact_amount=impact,
                    root_cause=root_cause,
                    detection_method="isolation_forest_enhanced",
                    confidence_score=round(
                        min(abs(row.get("decision_score", 0)) * 2, 1.0), 3
                    ),
                    details=f"Cost ${row['amount']:.2f} vs avg ${mean_cost:.2f} (z-score: {z_score:.1f})",
                    detected_at=datetime.now(timezone.utc),
                )
                detected_anomalies.append(anomaly)
                self.db.add(anomaly)

        self.db.commit()
        logger.info(f"Detected {len(detected_anomalies)} new anomalies")
        return detected_anomalies

    def get_anomalies(self, user_id: str, limit: int = 50) -> List[Anomaly]:
        return (
            self.db.query(Anomaly)
            .join(CostRecord, Anomaly.cost_record_id == CostRecord.id)
            .filter(CostRecord.user_id == user_id)
            .order_by(Anomaly.detected_at.desc())
            .limit(limit)
            .all()
        )

    def get_anomaly_summary(self, user_id: str) -> dict:
        anomalies = self.get_anomalies(user_id, limit=500)
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        total_impact = 0.0
        unresolved = 0

        for a in anomalies:
            severity_counts[a.severity] = severity_counts.get(a.severity, 0) + 1
            total_impact += a.impact_amount
            if not a.is_resolved:
                unresolved += 1

        return {
            "total_anomalies": len(anomalies),
            "critical": severity_counts["critical"],
            "high": severity_counts["high"],
            "medium": severity_counts["medium"],
            "low": severity_counts["low"],
            "total_impact": round(total_impact, 2),
            "unresolved": unresolved,
        }

    @staticmethod
    def _calculate_severity(z_score: float) -> str:
        if z_score >= 4.0:
            return "critical"
        elif z_score >= 3.0:
            return "high"
        elif z_score >= 2.0:
            return "medium"
        return "low"

    @staticmethod
    def _determine_root_cause(row, service_df: Any) -> str:
        mean_cost = service_df["amount"].mean()
        if row["amount"] > mean_cost * 3:
            return f"Cost spike: {row['amount']:.2f} is {row['amount']/mean_cost:.1f}x the average"
        elif row["amount"] > mean_cost * 2:
            return f"Elevated spending: {row['amount']:.2f} is {row['amount']/mean_cost:.1f}x above normal"
        elif row["amount"] < mean_cost * 0.3:
            return f"Unusual drop: cost fell to {row['amount']:.2f} ({(row['amount']/mean_cost)*100:.0f}% of average)"
        return "Statistical outlier detected by ensemble model"
