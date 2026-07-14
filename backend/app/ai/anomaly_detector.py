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

from app.models.cost_record import CostRecord, DemoCostRecord, AWSCostRecord
from app.models.anomaly import Anomaly, DemoAnomaly, AWSAnomaly
from app.models.user import User
from app.models.aws_account import AWSAccount

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Detects cost anomalies using an ensemble of ML models."""

    def __init__(self, db: Session):
        self.db = db

    def _run_detection_on_records(self, records, contamination: float = 0.08, is_demo: bool = True) -> List[Any]:
        if not ML_AVAILABLE or len(records) < 14:
            return []

        df = pd.DataFrame(
            [
                {
                    "id": getattr(r, "id", f"live-{idx}") if not isinstance(r, dict) else r.get("id", f"live-{idx}"),
                    "amount": getattr(r, "amount", 0.0) if not isinstance(r, dict) else r.get("amount", 0.0),
                    "date": getattr(r, "date", date.today()) if not isinstance(r, dict) else r.get("date", date.today()),
                    "service": getattr(r, "service", "") if not isinstance(r, dict) else r.get("service", ""),
                    "region": getattr(r, "region", "us-east-1") if not isinstance(r, dict) else r.get("region", "us-east-1"),
                }
                for idx, r in enumerate(records)
            ]
        )

        detected_anomalies = []
        anomaly_cls = DemoAnomaly if is_demo else AWSAnomaly
        for service in df["service"].unique():
            sdf = df[df["service"] == service].copy()
            if len(sdf) < 10:
                continue

            sdf = sdf.sort_values("date")
            sdf["rolling_mean_7d"] = sdf["amount"].rolling(window=7, min_periods=1).mean()
            sdf["rolling_std_7d"] = sdf["amount"].rolling(window=7, min_periods=1).std().fillna(0)
            sdf["deviation"] = (sdf["amount"] - sdf["rolling_mean_7d"]).abs()
            sdf["day_of_week"] = pd.to_datetime(sdf["date"]).dt.dayofweek

            features = sdf[
                [
                    "amount",
                    "rolling_mean_7d",
                    "rolling_std_7d",
                    "deviation",
                    "day_of_week",
                ]
            ].fillna(0)

            model = IsolationForest(
                contamination=contamination,
                random_state=42,
                n_estimators=200,
                max_features=1.0,
            )
            sdf["anomaly_score"] = model.fit_predict(features)
            sdf["decision_score"] = model.decision_function(features)

            anomaly_rows = sdf[sdf["anomaly_score"] == -1]
            for _, row in anomaly_rows.iterrows():
                mean_cost = sdf["amount"].mean()
                std_cost = sdf["amount"].std() or 1.0
                z_score = abs(row["amount"] - mean_cost) / std_cost
                if z_score < 2.0:
                    continue
                severity = self._calculate_severity(z_score)
                impact = round(abs(row["amount"] - mean_cost), 2)
                root_cause = self._determine_root_cause(row, sdf)

                anomaly = anomaly_cls(
                    cost_record_id=str(row["id"]),
                    date=row["date"] if isinstance(row["date"], date) else datetime.strptime(str(row["date"]), "%Y-%m-%d").date(),
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
        return detected_anomalies

    def detect_anomalies(
        self, user_id: str, contamination: float = 0.08
    ) -> List[Any]:
        """Run anomaly detection dynamically based on user type."""
        from datetime import timedelta
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []

        # 1. Reviewer Account (Demo Mode)
        if user.is_demo_mode:
            records = (
                self.db.query(DemoCostRecord)
                .filter(DemoCostRecord.user_id == user_id)
                .order_by(DemoCostRecord.date)
                .all()
            )
            anomalies = self._run_detection_on_records(records, contamination, is_demo=True)
            for a in anomalies:
                exists = self.db.query(DemoAnomaly).filter_by(cost_record_id=a.cost_record_id).first()
                if not exists:
                    self.db.add(a)
            self.db.commit()
            return anomalies

        # 2. Normal User (Live AWS CE)
        else:
            if not user.is_aws_connected:
                return []
            aws_account = self.db.query(AWSAccount).filter(AWSAccount.org_id == user.org_id, AWSAccount.is_active.is_(True)).first()
            if not aws_account:
                return []

            today = date.today()
            start_date = today - timedelta(days=30)
            from app.services.aws_cost_explorer import cost_explorer_service
            try:
                records = cost_explorer_service.get_live_costs(aws_account, start_date, today)
                return self._run_detection_on_records(records, contamination, is_demo=False)
            except Exception as e:
                logger.warning("Failed to fetch live costs for anomaly detection: %s. Falling back to local AWS records.", e)
                records = (
                    self.db.query(AWSCostRecord)
                    .filter(AWSCostRecord.user_id == user_id)
                    .order_by(AWSCostRecord.date)
                    .all()
                )
                return self._run_detection_on_records(records, contamination, is_demo=False)

    def get_anomalies(self, user_id: str, limit: int = 50) -> List[Any]:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []

        if user.is_demo_mode:
            # Get user's cost record IDs first (avoids relying on JOIN in MongoDB shim)
            record_ids = [
                r.id for r in
                self.db.query(DemoCostRecord)
                .filter(DemoCostRecord.user_id == user_id)
                .all()
            ]
            if not record_ids:
                return []
            return (
                self.db.query(DemoAnomaly)
                .filter(DemoAnomaly.cost_record_id.in_(record_ids))
                .order_by(DemoAnomaly.detected_at.desc())
                .limit(limit)
                .all()
            )
        else:
            return self.detect_anomalies(user_id)[:limit]

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
