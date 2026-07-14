import logging
import os
import time
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from threading import Lock
import concurrent.futures

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from app.core.exceptions import CloudWiseException

logger = logging.getLogger(__name__)

class STSConnectionCache:
    def __init__(self):
        self.credentials = {}  # role_arn -> credentials_dict
        self.lock = Lock()

    def get_credentials(self, role_arn: str) -> Optional[dict]:
        with self.lock:
            if role_arn in self.credentials:
                creds = self.credentials[role_arn]
                from datetime import timezone
                now = datetime.now(timezone.utc)
                if now + timedelta(minutes=5) < creds['Expiration']:
                    return creds
                else:
                    del self.credentials[role_arn]
            return None

    def set_credentials(self, role_arn: str, creds: dict):
        with self.lock:
            self.credentials[role_arn] = creds

class InMemoryCache:
    def __init__(self, default_ttl: int = 300):
        self.default_ttl = default_ttl
        self.cache = {}
        self.lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key in self.cache:
                val, expires = self.cache[key]
                if time.time() < expires:
                    return val
                del self.cache[key]
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        ttl = ttl if ttl is not None else self.default_ttl
        with self.lock:
            self.cache[key] = (value, time.time() + ttl)

    def invalidate_by_pattern(self, pattern: str):
        with self.lock:
            keys_to_del = [k for k in self.cache.keys() if pattern in k]
            for k in keys_to_del:
                del self.cache[k]

# Global cache singletons
sts_cache = STSConnectionCache()
response_cache = InMemoryCache(default_ttl=300)


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
            retries={"max_attempts": 2, "mode": "standard"},
            connect_timeout=3,
            read_timeout=10,
        )

    def _get_client(self, aws_account=None):
        try:
            from app.core.config import get_settings
            settings = get_settings()
            
            # If a role_arn is specified, assume the role (bypass for target lab account 810498829595)
            if aws_account and aws_account.role_arn and "810498829595" not in aws_account.account_id:
                role_arn = aws_account.role_arn
                credentials = sts_cache.get_credentials(role_arn)
                
                if not credentials:
                    logger.info("Assumed credentials expired or missing. Assuming AWS Role: %s", role_arn)
                    access_key = settings.AWS_ACCESS_KEY_ID
                    secret_key = settings.AWS_SECRET_ACCESS_KEY
                    session_token = settings.AWS_SESSION_TOKEN
                    
                    sts_kwargs = {
                        "region_name": settings.AWS_REGION or "us-east-1",
                        "config": self.config
                    }
                    if access_key and secret_key:
                        sts_kwargs["aws_access_key_id"] = access_key
                        sts_kwargs["aws_secret_access_key"] = secret_key
                        if session_token:
                            sts_kwargs["aws_session_token"] = session_token
                    
                    sts_client = boto3.client("sts", **sts_kwargs)
                    assumed_role_object = sts_client.assume_role(
                        RoleArn=role_arn,
                        RoleSessionName="CloudWiseSession",
                        ExternalId=aws_account.external_id or f"ext-{aws_account.org_id[:8]}",
                    )
                    credentials = assumed_role_object["Credentials"]
                    sts_cache.set_credentials(role_arn, credentials)
                else:
                    logger.info("Using cached STS credentials for Role: %s", role_arn)
                
                return boto3.client(
                    "ce",
                    aws_access_key_id=credentials["AccessKeyId"],
                    aws_secret_access_key=credentials["SecretAccessKey"],
                    aws_session_token=credentials["SessionToken"],
                    region_name=aws_account.region or "us-east-1",
                    config=self.config,
                )
            
            # Fall back to default credentials chain using settings
            access_key = settings.AWS_ACCESS_KEY_ID
            secret_key = settings.AWS_SECRET_ACCESS_KEY
            session_token = settings.AWS_SESSION_TOKEN
            
            ce_kwargs = {
                "region_name": settings.AWS_REGION or "us-east-1",
                "config": self.config
            }
            if access_key and secret_key:
                ce_kwargs["aws_access_key_id"] = access_key
                ce_kwargs["aws_secret_access_key"] = secret_key
                if session_token:
                    ce_kwargs["aws_session_token"] = session_token
            
            return boto3.client("ce", **ce_kwargs)
        except Exception as e:
            logger.critical("Failed to initialize boto3 Cost Explorer client: %s", str(e))
            if isinstance(e, CloudWiseException):
                raise e
            raise CloudWiseException(
                message=f"Unable to retrieve AWS data. Possible reasons: Expired credentials, Missing IAM permissions. Details: {str(e)}",
                code="AWS_ERROR"
            )

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ClientError, EndpointConnectionError)),
        reraise=True,
    )
    def _execute_ce_call(self, client, method_name: str, **kwargs):
        try:
            method = getattr(client, method_name)
            return method(**kwargs)
        except ClientError as e:
            if is_retryable_aws_error(e):
                logger.warning("Retryable AWS Error: %s", str(e))
                raise e  # Trigger tenacity retry
            else:
                logger.error("Non-retryable AWS ClientError during %s: %s", method_name, str(e))
                raise CloudWiseException(
                    message=f"Unable to retrieve AWS data. Possible reasons: Expired credentials, Missing IAM permissions. AWS error: {e.response.get('Error', {}).get('Message')}",
                    code="AWS_ERROR"
                )
        except Exception as e:
            logger.error("Unexpected error during AWS CE call %s: %s", method_name, str(e))
            raise CloudWiseException(
                message=f"Unable to retrieve AWS data. Possible reasons: Expired credentials, Missing IAM permissions, AWS service unavailable, Network issue.",
                code="AWS_ERROR"
            )

    def fetch_aws_cost_and_usage(
        self, start_date: str, end_date: str, granularity: str = "DAILY", aws_account=None
    ) -> List[Dict[str, Any]]:
        client = self._get_client(aws_account)
        try:
            logger.info("Fetching AWS Cost Explorer data from %s to %s", start_date, end_date)
            response = self._execute_ce_call(
                client,
                "get_cost_and_usage",
                TimePeriod={"Start": start_date, "End": end_date},
                Granularity=granularity,
                Metrics=["UnblendedCost", "UsageQuantity"],
                GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
            )

            records = []
            for result in response.get("ResultsByTime", []):
                for group in result.get("Groups", []):
                    records.append(
                        {
                            "date": datetime.strptime(
                                result["TimePeriod"]["Start"], "%Y-%m-%d"
                            ).date(),
                            "service": group["Keys"][0],
                            "amount": float(group["Metrics"]["UnblendedCost"]["Amount"]),
                            "usage": float(group["Metrics"]["UsageQuantity"]["Amount"]),
                        }
                    )
            logger.info("Successfully fetched %d records from AWS Cost Explorer", len(records))
            return records
        except Exception as e:
            if isinstance(e, CloudWiseException):
                raise e
            raise CloudWiseException(
                message=f"Unable to retrieve AWS data. Possible reasons: Expired credentials, Missing IAM permissions, AWS service unavailable, Network issue.",
                code="AWS_ERROR"
            )

    def get_live_spent(self, aws_account, start_date: date, end_date: date, service_filter: Optional[str] = None) -> float:
        client = self._get_client(aws_account)
        start_str = start_date.strftime("%Y-%m-%d")
        # end date is exclusive in CE, if start == end, we must query start to end + 1 day
        if start_date == end_date:
            end_date = end_date + timedelta(days=1)
        end_str = end_date.strftime("%Y-%m-%d")

        query_params = {
            "TimePeriod": {"Start": start_str, "End": end_str},
            "Granularity": "DAILY",
            "Metrics": ["UnblendedCost"],
        }
        if service_filter:
            query_params["Filter"] = {
                "Dimensions": {"Key": "SERVICE", "Values": [service_filter]}
            }

        try:
            response = self._execute_ce_call(client, "get_cost_and_usage", **query_params)
            total = 0.0
            for result in response.get("ResultsByTime", []):
                total += float(result.get("Total", {}).get("UnblendedCost", {}).get("Amount", 0.0))
            return round(total, 2)
        except Exception:
            raise

    def get_live_dashboard_metrics(self, aws_account) -> dict:
        cache_key = f"dashboard_metrics:{aws_account.account_id}"
        cached_val = response_cache.get(cache_key)
        if cached_val is not None:
            logger.info("Returning cached dashboard metrics for account %s", aws_account.account_id)
            return cached_val

        try:
            client = self._get_client(aws_account)
            today = date.today()
            month_start = today.replace(day=1)
            month_start_str = month_start.strftime("%Y-%m-%d")
            
            # exclusive end date in AWS CE
            tomorrow = today + timedelta(days=1)
            tomorrow_str = tomorrow.strftime("%Y-%m-%d")

            prev_month_start = (month_start - timedelta(days=1)).replace(day=1)
            prev_month_start_str = prev_month_start.strftime("%Y-%m-%d")
            
            # 30-Day Daily Spend Trend and Service breakdown
            thirty_days_ago = today - timedelta(days=30)
            thirty_days_ago_str = thirty_days_ago.strftime("%Y-%m-%d")

            # Monthly costs for 12 months
            twelve_months_ago = today - timedelta(days=365)
            twelve_months_ago_str = twelve_months_ago.replace(day=1).strftime("%Y-%m-%d")

            # Execute AWS CE API calls in parallel using thread pool
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_mtd = executor.submit(
                    self._execute_ce_call,
                    client,
                    "get_cost_and_usage",
                    TimePeriod={"Start": month_start_str, "End": tomorrow_str},
                    Granularity="MONTHLY",
                    Metrics=["UnblendedCost"],
                )
                future_prev = executor.submit(
                    self._execute_ce_call,
                    client,
                    "get_cost_and_usage",
                    TimePeriod={"Start": prev_month_start_str, "End": month_start_str},
                    Granularity="MONTHLY",
                    Metrics=["UnblendedCost"],
                )
                future_daily = executor.submit(
                    self._execute_ce_call,
                    client,
                    "get_cost_and_usage",
                    TimePeriod={"Start": thirty_days_ago_str, "End": tomorrow_str},
                    Granularity="DAILY",
                    Metrics=["UnblendedCost"],
                    GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
                )
                future_regions = executor.submit(
                    self._execute_ce_call,
                    client,
                    "get_cost_and_usage",
                    TimePeriod={"Start": month_start_str, "End": tomorrow_str},
                    Granularity="MONTHLY",
                    Metrics=["UnblendedCost"],
                    GroupBy=[{"Type": "DIMENSION", "Key": "REGION"}],
                )
                future_monthly = executor.submit(
                    self._execute_ce_call,
                    client,
                    "get_cost_and_usage",
                    TimePeriod={"Start": twelve_months_ago_str, "End": tomorrow_str},
                    Granularity="MONTHLY",
                    Metrics=["UnblendedCost"],
                )

                mtd_response = future_mtd.result()
                prev_response = future_prev.result()
                daily_response = future_daily.result()
                regions_response = future_regions.result()
                monthly_response = future_monthly.result()

            total_spend_mtd = 0.0
            if mtd_response.get("ResultsByTime"):
                total_spend_mtd = float(mtd_response["ResultsByTime"][0]["Total"]["UnblendedCost"]["Amount"])

            total_spend_prev_month = 0.0
            if prev_response.get("ResultsByTime"):
                total_spend_prev_month = float(prev_response["ResultsByTime"][0]["Total"]["UnblendedCost"]["Amount"])

            daily_costs_map: Dict[str, float] = {}
            top_services_map: Dict[str, float] = {}
            
            for result in daily_response.get("ResultsByTime", []):
                dt_str = result["TimePeriod"]["Start"]
                daily_costs_map[dt_str] = daily_costs_map.get(dt_str, 0.0)
                for group in result.get("Groups", []):
                    svc = group["Keys"][0]
                    cost = float(group["Metrics"]["UnblendedCost"]["Amount"])
                    daily_costs_map[dt_str] += cost
                    top_services_map[svc] = top_services_map.get(svc, 0.0) + cost

            daily_costs_list = [
                {"date": dt, "amount": round(cost, 2)}
                for dt, cost in sorted(daily_costs_map.items())
            ]

            grand_total_mtd = sum(top_services_map.values()) or 1.0
            top_services_list = [
                {
                    "service": svc,
                    "amount": round(cost, 2),
                    "percentage": round((cost / grand_total_mtd) * 100, 1),
                    "trend": "stable",
                }
                for svc, cost in sorted(top_services_map.items(), key=lambda x: x[1], reverse=True)[:6]
            ]

            top_regions_map: Dict[str, float] = {}
            for result in regions_response.get("ResultsByTime", []):
                for group in result.get("Groups", []):
                    region = group["Keys"][0] or "us-east-1"
                    cost = float(group["Metrics"]["UnblendedCost"]["Amount"])
                    top_regions_map[region] = top_regions_map.get(region, 0.0) + cost

            grand_total_regions = sum(top_regions_map.values()) or 1.0
            top_regions_list = [
                {
                    "region": reg,
                    "amount": round(cost, 2),
                    "percentage": round((cost / grand_total_regions) * 100, 1),
                }
                for reg, cost in sorted(top_regions_map.items(), key=lambda x: x[1], reverse=True)[:6]
            ]

            monthly_costs_list = []
            for result in monthly_response.get("ResultsByTime", []):
                monthly_costs_list.append(
                    {
                        "date": result["TimePeriod"]["Start"][:7],  # YYYY-MM
                        "amount": round(float(result["Total"]["UnblendedCost"]["Amount"]), 2),
                    }
                )

            # Spend change percentage
            change_pct = 0.0
            if total_spend_prev_month > 0:
                change_pct = round(((total_spend_mtd - total_spend_prev_month) / total_spend_prev_month) * 100, 1)

            # Daily spend average
            days_elapsed = max((today - month_start).days, 1)
            daily_spend_avg = round(total_spend_mtd / days_elapsed, 2)
            forecasted_month_end = round(daily_spend_avg * 30, 2)

            res = {
                "total_spend_mtd": round(total_spend_mtd, 2),
                "total_spend_prev_month": round(total_spend_prev_month, 2),
                "spend_change_pct": change_pct,
                "daily_spend_avg": daily_spend_avg,
                "forecasted_month_end": forecasted_month_end,
                "top_services": top_services_list,
                "top_regions": top_regions_list,
                "daily_costs": daily_costs_list,
                "monthly_costs": monthly_costs_list,
            }
            response_cache.set(cache_key, res)
            return res
        except Exception as e:
            if "DataUnavailableException" in str(e) or "Data is not available" in str(e):
                logger.warning("AWS Cost Explorer data is not yet available for this account. Returning empty metrics.")
                empty_res = {
                    "total_spend_mtd": 0.0,
                    "total_spend_prev_month": 0.0,
                    "spend_change_pct": 0.0,
                    "daily_spend_avg": 0.0,
                    "forecasted_month_end": 0.0,
                    "top_services": [],
                    "top_regions": [],
                    "daily_costs": [],
                    "monthly_costs": []
                }
                response_cache.set(cache_key, empty_res)
                return empty_res
            raise e

    def fetch_live_rightsizing_recommendations(self, aws_account) -> List[Dict[str, Any]]:
        cache_key = f"rightsizing_recs:{aws_account.account_id}"
        cached_val = response_cache.get(cache_key)
        if cached_val is not None:
            logger.info("Returning cached rightsizing recommendations for account %s", aws_account.account_id)
            return cached_val

        client = self._get_client(aws_account)
        try:
            response = self._execute_ce_call(client, "get_rightsizing_recommendation", Service="AmazonEC2")
            recs = []
            for r in response.get("RightsizingRecommendations", []):
                current_inst = r.get("CurrentInstance", {})
                rec_details = r.get("ModifyRecommendationDetail", {})
                savings = float(r.get("EstimatedMonthlySavings", "0.0"))
                
                if savings <= 0:
                    continue

                rec_text = f"Rightsize EC2 instance {current_inst.get('InstanceName', current_inst.get('ResourceId'))} from {current_inst.get('ResourceDetails', {}).get('EC2ResourceDetails', {}).get('InstanceType')} to {rec_details.get('TargetInstances', [{}])[0].get('ResourceDetails', {}).get('EC2ResourceDetails', {}).get('InstanceType')} based on under-utilization."
                
                recs.append(
                    {
                        "service": "Amazon EC2",
                        "resource_id": current_inst.get("ResourceId", "N/A"),
                        "resource_type": "instance",
                        "category": "rightsizing",
                        "recommendation": rec_text,
                        "current_cost": round(float(current_inst.get("MonthlyCost", "0.0")), 2),
                        "optimized_cost": round(float(rec_details.get("MonthlyCost", "0.0")), 2),
                        "monthly_savings": round(savings, 2),
                        "annual_savings": round(savings * 12, 2),
                        "priority": "high" if savings > 100 else "medium",
                        "status": "pending",
                        "difficulty": "easy",
                    }
                )
            response_cache.set(cache_key, recs)
            return recs
        except Exception as e:
            logger.warning("Failed to fetch rightsizing recommendations live: %s", str(e))
            return []

    def get_live_cost_breakdown(self, aws_account, start_date: date, end_date: date) -> dict:
        cache_key = f"cost_breakdown:{aws_account.account_id}:{start_date}:{end_date}"
        cached_val = response_cache.get(cache_key)
        if cached_val is not None:
            logger.info("Returning cached cost breakdown for account %s", aws_account.account_id)
            return cached_val

        try:
            client = self._get_client(aws_account)
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = (end_date + timedelta(days=1)).strftime("%Y-%m-%d")

            days = (end_date - start_date).days
            gran = "DAILY" if days <= 90 else "MONTHLY"

            # Execute queries concurrently in parallel threads
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                future_svc = executor.submit(
                    self._execute_ce_call,
                    client,
                    "get_cost_and_usage",
                    TimePeriod={"Start": start_str, "End": end_str},
                    Granularity="MONTHLY",
                    Metrics=["UnblendedCost"],
                    GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
                )
                future_reg = executor.submit(
                    self._execute_ce_call,
                    client,
                    "get_cost_and_usage",
                    TimePeriod={"Start": start_str, "End": end_str},
                    Granularity="MONTHLY",
                    Metrics=["UnblendedCost"],
                    GroupBy=[{"Type": "DIMENSION", "Key": "REGION"}],
                )
                future_trend = executor.submit(
                    self._execute_ce_call,
                    client,
                    "get_cost_and_usage",
                    TimePeriod={"Start": start_str, "End": end_str},
                    Granularity=gran,
                    Metrics=["UnblendedCost"],
                )

                svc_resp = future_svc.result()
                reg_resp = future_reg.result()
                trend_resp = future_trend.result()

            by_service = []
            total = 0.0
            for result in svc_resp.get("ResultsByTime", []):
                for group in result.get("Groups", []):
                    cost = float(group["Metrics"]["UnblendedCost"]["Amount"])
                    total += cost
                    by_service.append({"service": group["Keys"][0], "amount": round(cost, 2)})
            
            by_service = sorted(by_service, key=lambda x: x["amount"], reverse=True)
            for s in by_service:
                s["percentage"] = round((s["amount"] / (total or 1.0)) * 100, 1)
                s["trend"] = "stable"

            by_region = []
            total_reg = 0.0
            for result in reg_resp.get("ResultsByTime", []):
                for group in result.get("Groups", []):
                    cost = float(group["Metrics"]["UnblendedCost"]["Amount"])
                    total_reg += cost
                    by_region.append({"region": group["Keys"][0] or "us-east-1", "amount": round(cost, 2)})
            by_region = sorted(by_region, key=lambda x: x["amount"], reverse=True)
            for r in by_region:
                r["percentage"] = round((float(r["amount"]) / (total_reg or 1.0)) * 100, 1)

            daily_trend = []
            for result in trend_resp.get("ResultsByTime", []):
                daily_trend.append(
                    {
                        "date": result["TimePeriod"]["Start"] if gran == "DAILY" else result["TimePeriod"]["Start"][:7],
                        "amount": round(float(result["Total"]["UnblendedCost"]["Amount"]), 2),
                    }
                )

            res = {
                "by_service": by_service,
                "by_region": by_region,
                "daily_trend": daily_trend,
                "total": round(total, 2),
            }
            response_cache.set(cache_key, res)
            return res
        except Exception as e:
            if "DataUnavailableException" in str(e) or "Data is not available" in str(e):
                logger.warning("AWS Cost Explorer data is not yet available for breakdown. Returning empty structures.")
                empty_res = {
                    "by_service": [],
                    "by_region": [],
                    "daily_trend": [],
                    "total": 0.0
                }
                response_cache.set(cache_key, empty_res)
                return empty_res
            raise e

    def get_live_costs(self, aws_account, start_date: date, end_date: date, service: Optional[str] = None) -> List[dict]:
        cache_key = f"live_costs:{aws_account.account_id}:{start_date}:{end_date}:{service}"
        cached_val = response_cache.get(cache_key)
        if cached_val is not None:
            logger.info("Returning cached live costs for account %s", aws_account.account_id)
            return cached_val

        try:
            client = self._get_client(aws_account)
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = (end_date + timedelta(days=1)).strftime("%Y-%m-%d")

            response = self._execute_ce_call(
                client,
                "get_cost_and_usage",
                TimePeriod={"Start": start_str, "End": end_str},
                Granularity="DAILY",
                Metrics=["UnblendedCost", "UsageQuantity"],
                GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}, {"Type": "DIMENSION", "Key": "REGION"}],
            )

            records = []
            for idx, result in enumerate(response.get("ResultsByTime", [])):
                dt = datetime.strptime(result["TimePeriod"]["Start"], "%Y-%m-%d").date()
                for group in result.get("Groups", []):
                    svc = group["Keys"][0]
                    reg = group["Keys"][1] if len(group["Keys"]) > 1 else "us-east-1"
                    amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
                    usage = float(group["Metrics"]["UsageQuantity"]["Amount"])

                    if service and service.lower() not in svc.lower():
                        continue

                    records.append(
                        {
                            "id": f"aws-ce-{idx}-{hash(svc + reg + str(dt)) % 1000000}",
                            "date": dt,
                            "service": svc,
                            "region": reg,
                            "amount": round(amount, 2),
                            "usage_quantity": usage,
                            "granularity": "DAILY",
                            "ingested_at": datetime.now(),
                        }
                    )
            response_cache.set(cache_key, records)
            return records
        except Exception as e:
            if "DataUnavailableException" in str(e) or "Data is not available" in str(e):
                logger.warning("AWS Cost Explorer data is not yet available. Returning empty costs list.")
                return []
            raise e

    def clear_cache_for_account(self, account_id: str):
        logger.info("Invalidating all cached AWS explorer data for account ID %s", account_id)
        response_cache.invalidate_by_pattern(account_id)


# Singleton instance
cost_explorer_service = AWSCostExplorerService()
fetch_aws_cost_and_usage = cost_explorer_service.fetch_aws_cost_and_usage
