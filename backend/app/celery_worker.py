import logging
from celery import Celery
import os
from app.core.config import get_settings
import app.tasks.scheduled

settings = get_settings()
logger = logging.getLogger(__name__)

celery_app = Celery(
    "cloudwise_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task
def generate_weekly_report():
    logger.info("Generating weekly cost report...")
    return "Report generated successfully"


@celery_app.task
def check_budget_alerts():
    logger.info("Checking for budget breaches...")
    return "Budget check complete"


# Register scheduled tasks
