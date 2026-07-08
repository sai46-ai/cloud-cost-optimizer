import logging
import os
from datetime import datetime
from typing import List, Dict, Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = logging.getLogger(__name__)


def is_retryable_aws_error(exception):
    if isinstance(exception, ClientError):
        code = exception.response.get("Error", {}).get("Code")
        return code in [
            "ThrottlingException",
            "TooManyRequestsException",
            "InternalErrorException",
        ]
    if isinstance(exception, EndpointConnectionError):
        return True
    return False


class AWSCostExplorerService:
    def __init__(self):
        self.config = Config(
            retries={"max_attempts": 5, "mode": "adaptive"},
            connect_timeout=10,
            read_timeout=30,
        )

    def _get_client(self):
        try:
            return boto3.client(
                "ce",
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
                region_name=os.getenv("AWS_REGION", "us-east-1"),
                config=self.config,
            )
        except Exception as e:
            logger.error("Failed to initialize boto3 Cost Explorer client: %s", str(e))
            return None

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ClientError, EndpointConnectionError)),
        reraise=True,
    )
    def _execute_fetch(self, client, start_date: str, end_date: str, granularity: str):
        try:
            response = client.get_cost_and_usage(
                TimePeriod={"Start": start_date, "End": end_date},
                Granularity=granularity,
                Metrics=["UnblendedCost", "UsageQuantity"],
                GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
            )
            return response
        except ClientError as e:
            if is_retryable_aws_error(e):
                logger.warning("Retryable AWS Error: %s", str(e))
                raise e  # Trigger tenacity retry
            else:
                logger.error("Non-retryable AWS ClientError: %s", str(e))
                return None

    def fetch_aws_cost_and_usage(
        self, start_date: str, end_date: str, granularity: str = "DAILY"
    ) -> List[Dict[str, Any]]:
        client = self._get_client()
        if not client:
            return []

        try:
            logger.info(
                "Fetching AWS Cost Explorer data from %s to %s", start_date, end_date
            )
            response = self._execute_fetch(client, start_date, end_date, granularity)

            if not response:
                return []

            records = []
            for result in response.get("ResultsByTime", []):
                for group in result.get("Groups", []):
                    records.append(
                        {
                            "date": datetime.strptime(
                                result["TimePeriod"]["Start"], "%Y-%m-%d"
                            ).date(),
                            "service": group["Keys"][0],
                            "amount": float(
                                group["Metrics"]["UnblendedCost"]["Amount"]
                            ),
                            "usage": float(group["Metrics"]["UsageQuantity"]["Amount"]),
                        }
                    )
            logger.info(
                "Successfully fetched %d records from AWS Cost Explorer", len(records)
            )
            return records

        except NoCredentialsError:
            logger.error(
                "AWS credentials not found. Ensure environment variables or IAM roles are set."
            )
            return []
        except Exception as e:
            logger.critical(
                "Unexpected error during AWS Cost Explorer fetch: %s",
                str(e),
                exc_info=True,
            )
            return []


# Singleton instance
cost_explorer_service = AWSCostExplorerService()
fetch_aws_cost_and_usage = cost_explorer_service.fetch_aws_cost_and_usage
