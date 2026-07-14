"""
CloudWise AI - Domain Models Package
All SQLAlchemy ORM models for the application.
"""

from app.models.user import User, DemoUser
from app.models.organization import Organization
from app.models.aws_account import AWSAccount, AWSResource, AWSBilling, AWSAlert, DemoAlert
from app.models.cost_record import CostRecord, DemoCostRecord, AWSCostRecord
from app.models.budget import Budget, DemoBudget, AWSBudget
from app.models.anomaly import Anomaly, DemoAnomaly, AWSAnomaly
from app.models.recommendation import Recommendation, DemoRecommendation, AWSRecommendation
from app.models.forecast import Forecast, DemoForecast, AWSForecast
from app.models.report import Report, DemoReport, AWSReport
from app.models.audit_log import AuditLog
from app.models.settings import UserSettings

__all__ = [
    "User",
    "DemoUser",
    "Organization",
    "AWSAccount",
    "AWSResource",
    "AWSBilling",
    "AWSAlert",
    "DemoAlert",
    "CostRecord",
    "DemoCostRecord",
    "AWSCostRecord",
    "Budget",
    "DemoBudget",
    "AWSBudget",
    "Anomaly",
    "DemoAnomaly",
    "AWSAnomaly",
    "Recommendation",
    "DemoRecommendation",
    "AWSRecommendation",
    "Forecast",
    "DemoForecast",
    "AWSForecast",
    "Report",
    "DemoReport",
    "AWSReport",
    "AuditLog",
    "UserSettings",
]
