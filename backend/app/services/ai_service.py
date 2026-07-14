"""
AI Service Layer
Centralized service for managing all AI interactions and provider integrations (Google Gemini API).
"""

import logging
import asyncio
import json
from typing import Optional, Generator, Dict, Any, List, AsyncGenerator
from sqlalchemy.orm import Session
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import get_settings
from app.services.cost_service import CostService
from app.models.anomaly import Anomaly
from app.models.cost_record import CostRecord
from app.models.user import User

logger = logging.getLogger(__name__)
settings = get_settings()

# Pre-built FinOps knowledge base for rule-based fallback
FINOPS_KB = {
    "reduce costs": "Here are top strategies to reduce AWS costs:\n1. **Right-size instances** — Match EC2/RDS instance types to actual workload needs\n2. **Use Reserved Instances / Savings Plans** — Commit for 1-3 years for 30-72% savings\n3. **Enable S3 Intelligent-Tiering** — Automatic storage class optimization\n4. **Delete idle resources** — Remove unattached EBS volumes, unused EIPs, idle load balancers\n5. **Schedule non-production workloads** — Stop dev/staging instances overnight\n6. **Use Spot Instances** — For fault-tolerant workloads, save up to 90%\n7. **Implement lifecycle policies** — Auto-archive old S3 objects to Glacier",
    "expensive service": "To find your most expensive AWS service, check the **Cost Analytics** page. Typically, the top cost drivers are:\n1. **Amazon EC2** (compute) — Usually 40-60% of total spend\n2. **Amazon RDS** (databases) — 15-25% of spend\n3. **Amazon S3** (storage) — 5-15% of spend\n4. **Data Transfer** — Often an overlooked cost driver",
    "ec2 spending": "EC2 spending can increase due to:\n- **Auto-scaling events** adding more instances\n- **Instance type changes** (upsizing)\n- **New deployments** or workload migrations\n- **Forgotten dev/test instances** running 24/7\n\nCheck the **Resource Optimization** page for idle EC2 instances and rightsizing recommendations.",
    "predict": "I can predict your future AWS costs using time-series analysis. Check the **AI Insights** page for:\n- Next day forecast\n- Next week forecast\n- Next month forecast\n- Next quarter forecast\n\nForecasts include confidence intervals to show the range of expected spending.",
    "anomaly": "Cost anomalies are detected using Isolation Forest ML algorithm. When spending deviates significantly from normal patterns, we flag it with:\n- **Severity** (critical/high/medium/low)\n- **Impact amount** ($ deviation from baseline)\n- **Root cause analysis** (likely reason for the anomaly)\n\nCheck the **AI Insights** page for current anomalies.",
    "budget": "You can manage budgets from the **Budgets** page:\n- Create budgets with custom thresholds (50%, 80%, 90%, 100%)\n- Get alerts via email, dashboard, or SNS\n- Track spending vs. budget in real-time\n- Set daily, weekly, or monthly periods",
}


class AIService:
    """Centralized AI Service using Google Gemini."""

    def __init__(self, db: Session):
        self.db = db
        self.cost_service = CostService(db)

    async def chat(self, message: str, user_id: Optional[str] = None) -> dict:
        """Process a user message and return a response using Google Gemini."""
        message_lower = message.lower().strip()

        try:
            response = await self._gemini_response(message, user_id)
            return {
                "response": response,
                "source": "gemini_ai",
                "suggestions": self._get_suggestions(message_lower),
            }
        except Exception as e:
            logger.warning(f"Gemini API call failed: {e}")

        # Rule-based fallback if Gemini API call fails at runtime
        response = self._rule_based_response(message_lower, user_id)
        return {
            "response": response,
            "source": "knowledge_base",
            "suggestions": self._get_suggestions(message_lower),
        }

    def _get_active_anomalies(self, user_id: Optional[str]) -> list[Any]:
        """Fetch unresolved anomalies from the database for the user."""
        if not user_id:
            return []
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        try:
            if user.is_demo_mode:
                from app.models.anomaly import DemoAnomaly
                from app.models.cost_record import DemoCostRecord
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
                    .filter(DemoAnomaly.is_resolved.is_(False))
                    .all()
                )
            else:
                from app.models.anomaly import AWSAnomaly
                from app.models.cost_record import AWSCostRecord
                record_ids = [
                    r.id for r in
                    self.db.query(AWSCostRecord)
                    .filter(AWSCostRecord.user_id == user_id)
                    .all()
                ]
                if not record_ids:
                    return []
                return (
                    self.db.query(AWSAnomaly)
                    .filter(AWSAnomaly.cost_record_id.in_(record_ids))
                    .filter(AWSAnomaly.is_resolved.is_(False))
                    .all()
                )

        except Exception as e:
            logger.error(f"Error querying active anomalies for chat: {e}")
            return []

    def _rule_based_response(self, message: str, user_id: Optional[str]) -> str:
        """Match user query to knowledge base entries with active db context."""
        # 1. Anomaly / cost spike queries
        is_spike_query = any(
            w in message
            for w in [
                "spike",
                "anomaly",
                "unusual",
                "increase",
                "jump",
                "high",
                "rise",
                "deviation",
                "outlier",
            ]
        )
        if is_spike_query:
            active_anomalies = self._get_active_anomalies(user_id)
            mentioned_service = None
            if "ec2" in message or "compute" in message:
                mentioned_service = "Amazon EC2"
            elif "rds" in message or "database" in message:
                mentioned_service = "Amazon RDS"
            elif "s3" in message or "storage" in message:
                mentioned_service = "Amazon S3"

            if mentioned_service:
                service_anomaly = next(
                    (
                        a
                        for a in active_anomalies
                        if mentioned_service.lower() in a.service.lower()
                    ),
                    None,
                )
                if service_anomaly:
                    return (
                        f"⚠️ **Cost Anomaly Detected in {service_anomaly.service}:**\n\n"
                        f"- **Date:** {service_anomaly.date}\n"
                        f"- **Severity:** **{service_anomaly.severity.upper()}**\n"
                        f"- **Estimated Financial Impact:** +${service_anomaly.impact_amount:,.2f}\n"
                        f"- **Root Cause:** {service_anomaly.root_cause}\n"
                        f"- **Details:** {service_anomaly.details or 'No additional details available.'}\n\n"
                        f"Check the **Resource Optimizer** page for optimization recommendations related to {service_anomaly.service}."
                    )
                else:
                    if mentioned_service == "Amazon EC2":
                        return FINOPS_KB["ec2 spending"]
                    elif mentioned_service == "Amazon RDS":
                        return (
                            "RDS costs typically spike due to:\n"
                            "- Provisioning larger DB instances than required (over-provisioning)\n"
                            "- High storage allocation or unoptimized backup retention policies\n"
                            "- Read/Write IOPS spikes under database load\n\n"
                            "Check the **Resource Optimizer** page for RDS rightsizing recommendations."
                        )
                    elif mentioned_service == "Amazon S3":
                        return (
                            "S3 cost spikes are often caused by:\n"
                            "- Missing lifecycle rules leading to accumulating historical object versions\n"
                            "- Unexpected massive data ingestion or lack of compression\n"
                            "- Extremely high volume of API requests (GET/PUT)\n\n"
                            "Check the **Resource Optimizer** page for S3 lifecycle recommendations."
                        )

            if "anomaly" in message or "spike" in message or "unusual" in message:
                if active_anomalies:
                    response_parts = ["🔍 **Current Active Cost Anomalies:**\n"]
                    for idx, a in enumerate(active_anomalies, 1):
                        response_parts.append(
                            f"{idx}. **{a.service}** on {a.date} ({a.severity.upper()} severity):\n"
                            f"   - **Impact:** +${a.impact_amount:,.2f}\n"
                            f"   - **Root Cause:** {a.root_cause}\n"
                        )
                    response_parts.append(
                        "\nYou can review these details and run a manual detection scan on the **AI Insights** page."
                    )
                    return "\n".join(response_parts)
                else:
                    return "✅ No active cost anomalies detected. Your cloud spending is currently in line with baseline expectations."

        # 2. Check for keyword matches in FINOPS_KB
        for key, response in FINOPS_KB.items():
            if key in message:
                return response

        # 3. Cost-related queries
        if any(w in message for w in ["cost", "spend", "bill", "charge", "price"]):
            return self._get_cost_context(user_id)

        # 4. AWS Academy credentials and IAM info
        if any(
            w in message
            for w in [
                "iam",
                "access key",
                "credentials",
                "academy",
                "voclabs",
                "connect",
                "integrate",
            ]
        ):
            return (
                "⚠️ **AWS Academy Credentials Constraint:**\n\n"
                "Creating a permanent IAM user or generating long-term AWS Access Keys will fail in this environment "
                "because the **AWS Academy Learner Lab** operates under a restricted **voclabs** role. "
                "Administrative actions such as `iam:CreateUser` are not permitted.\n\n"
                "**Solution:**\n"
                "You must use the temporary AWS credentials provided by your AWS Academy console session. "
                "Configure your environment using the following temporary keys:\n"
                "- `AWS_ACCESS_KEY_ID`\n"
                "- `AWS_SECRET_ACCESS_KEY`\n"
                "- `AWS_SESSION_TOKEN` (Must be included for temporary session validation)"
            )

        # 5. Greeting
        if any(w in message for w in ["hello", "hi", "hey", "help"]):
            return (
                "👋 Hi! I'm your AI FinOps Assistant powered by Google Gemini. I can help you with:\n\n"
                "- **Explain your AWS bill** — Ask about costs, services, or spending trends\n"
                "- **Anomaly analysis** — Understand unusual spending patterns\n"
                "- **Optimization tips** — Get recommendations to reduce costs\n"
                "- **Forecasting** — Predict future cloud spending\n"
                "- **Budget management** — Set up and track budgets\n\n"
                'Try asking: *"Why did EC2 costs spike?"* or *"How can I reduce costs?"*'
            )

        return (
            "I can help you understand your AWS costs and find savings opportunities. "
            "Try asking about:\n\n"
            "- Cost trends and breakdowns\n"
            "- Anomaly explanations\n"
            "- Optimization recommendations\n"
            "- Spending forecasts\n"
            "- Budget setup and alerts"
        )

    def _get_cost_context(self, user_id: Optional[str]) -> str:
        """Build a response with current cost data context."""
        if not user_id:
            return "Please log in to view your cost context."
        try:
            metrics = self.cost_service.get_dashboard_metrics(user_id)
            return (
                f"📊 **Your Current AWS Spending:**\n\n"
                f"- **Month-to-date:** ${metrics.total_spend_mtd:,.2f}\n"
                f"- **Previous month:** ${metrics.total_spend_prev_month:,.2f}\n"
                f"- **Change:** {metrics.spend_change_pct:+.1f}%\n"
                f"- **Daily average:** ${metrics.daily_spend_avg:,.2f}\n"
                f"- **Forecasted month-end:** ${metrics.forecasted_month_end:,.2f}\n"
                f"- **Savings opportunity:** ${metrics.total_savings_opportunity:,.2f}\n\n"
                f"Top spending services:\n"
                + "\n".join(
                    f"  • {s.service}: ${s.amount:,.2f} ({s.percentage:.1f}%)"
                    for s in metrics.top_services[:5]
                )
            )
        except Exception as e:
            logger.error(f"Error fetching cost context: {e}")
            return "I'd be happy to help with your AWS costs. Please check the **Dashboard** for current spending data."

    async def _gemini_response(self, message: str, user_id: Optional[str] = None) -> str:
        """Generate response using Google Gemini API."""
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.strip() == "" or "placeholder" in settings.GEMINI_API_KEY.lower() or "mock" in settings.GEMINI_API_KEY.lower():
            raise Exception("Gemini API key is not configured or is invalid.")

        system_prompt = (
            "You are CloudWise AI, an expert FinOps assistant specializing in AWS cost optimization and cloud economics. "
            "Provide concise, actionable advice about AWS billing, cost optimization, rightsizing, and cloud architecture. "
            "Use clear markdown formatting. Be specific with AWS service names and pricing details.\n\n"
            "CRITICAL ENVIRONMENT CONSTRAINTS:\n"
            "Note that this environment uses AWS Academy Accounts. Creating permanent IAM users or generating long-term "
            "AWS Access Keys is NOT permitted because AWS Academy Learner Lab operates under a restricted 'voclabs' role. "
            "Advise users to supply temporary credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_SESSION_TOKEN) when requested."
        )

        # Inject live context if available
        if user_id:
            cost_info = self._get_cost_context(user_id)
            system_prompt += f"\n\nCURRENT USER COST DATA:\n{cost_info}"
            
            active_anomalies = self._get_active_anomalies(user_id)
            if active_anomalies:
                anomaly_info = "\n".join(
                    f"- Service: {a.service}, Severity: {a.severity}, Impact: +${a.impact_amount:,.2f}, Cause: {a.root_cause}"
                    for a in active_anomalies
                )
                system_prompt += f"\n\nACTIVE COST ANOMALIES:\n{anomaly_info}"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
        payload = {
            "contents": [
                {"parts": [{"text": f"{system_prompt}\n\nUser Question: {message}"}]}
            ]
        }

        try:
            data = await self._call_gemini_api(url, payload)
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
            raise Exception("Invalid or empty response format from Gemini API")
        except Exception as e:
            logger.error(f"Gemini API invocation failed: {e}")
            raise e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=6),
        retry=retry_if_exception_type(httpx.HTTPStatusError),
        reraise=True
    )
    async def _call_gemini_api(self, url: str, payload: dict) -> dict:
        """Call Gemini API with retry on transient status errors (429, 5xx)."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code in [429, 500, 502, 503, 504]:
                logger.warning(f"Transient error from Gemini API: {resp.status_code}. Retrying...")
                resp.raise_for_status()
            elif resp.status_code != 200:
                logger.error(f"Non-retryable Gemini error: {resp.status_code} - {resp.text}")
                resp.raise_for_status()
            return resp.json()

    async def chat_stream(
        self, message: str, user_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Stream chat responses from Google Gemini API, falling back to rule-based KB on failure."""
        system_prompt = (
            "You are CloudWise AI, an expert FinOps assistant specializing in AWS cost optimization and cloud economics. "
            "Provide concise, actionable advice about AWS billing, cost optimization, rightsizing, and cloud architecture. "
            "Use clear markdown formatting. Be specific with AWS service names and pricing details.\n\n"
            "CRITICAL ENVIRONMENT CONSTRAINTS:\n"
            "Note that this environment uses AWS Academy Accounts. Creating permanent IAM users or generating long-term "
            "AWS Access Keys is NOT permitted because AWS Academy Learner Lab operates under a restricted 'voclabs' role. "
            "Advise users to supply temporary credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_SESSION_TOKEN) when requested."
        )

        if user_id:
            cost_info = self._get_cost_context(user_id)
            system_prompt += f"\n\nCURRENT USER COST DATA:\n{cost_info}"
            active_anomalies = self._get_active_anomalies(user_id)
            if active_anomalies:
                anomaly_info = "\n".join(
                    f"- Service: {a.service}, Severity: {a.severity}, Impact: +${a.impact_amount:,.2f}, Cause: {a.root_cause}"
                    for a in active_anomalies
                )
                system_prompt += f"\n\nACTIVE COST ANOMALIES:\n{anomaly_info}"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:streamGenerateContent?key={settings.GEMINI_API_KEY}"
        payload = {
            "contents": [
                {"parts": [{"text": f"{system_prompt}\n\nUser Question: {message}"}]}
            ]
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        raise Exception(f"Gemini error status: {response.status_code}")
                    
                    buffer = ""
                    async for chunk in response.aiter_text():
                        buffer += chunk
                        while True:
                            buffer = buffer.strip()
                            if not buffer:
                                break
                            start = buffer.find("{")
                            if start == -1:
                                break
                            brace_count = 0
                            end = -1
                            for i in range(start, len(buffer)):
                                if buffer[i] == "{":
                                    brace_count += 1
                                elif buffer[i] == "}":
                                    brace_count -= 1
                                    if brace_count == 0:
                                        end = i
                                        break
                            if end == -1:
                                break
                            
                            obj_str = buffer[start:end+1]
                            buffer = buffer[end+1:]
                            try:
                                obj = json.loads(obj_str)
                                text = obj["candidates"][0]["content"]["parts"][0]["text"]
                                if text:
                                    yield json.dumps({"text": text, "source": "gemini_ai"})
                            except Exception:
                                pass
            return
        except Exception as e:
            logger.warning(f"Gemini stream failed: {e}")

        # Fallback to rule-based response
        fallback = self._rule_based_response(message.lower().strip(), user_id)
        for chunk in self._split_text_to_chunks(fallback):
            yield json.dumps({"text": chunk, "source": "knowledge_base"})
            await asyncio.sleep(0.01)

    def _split_text_to_chunks(self, text: str, chunk_size: int = 10) -> list[str]:
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

    def _get_suggestions(self, message: str) -> list:
        """Return follow-up question suggestions based on context."""
        if any(w in message for w in ["cost", "spend", "bill"]):
            return [
                "What is my most expensive service?",
                "How can I reduce costs?",
                "Predict next month's bill",
            ]
        if any(w in message for w in ["anomaly", "spike", "unusual"]):
            return [
                "Show me all anomalies",
                "Why did EC2 costs spike?",
                "How to prevent cost spikes?",
            ]
        return [
            "Show my current spending",
            "How can I reduce costs?",
            "Predict next month's bill",
            "What anomalies were detected?",
        ]
