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

from app.core.config import get_settings
from app.services.cost_service import CostService
from app.models.anomaly import Anomaly
from app.models.cost_record import CostRecord

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
    """Centralized AI Service using Google Gemini and OpenAI APIs."""

    def __init__(self, db: Session):
        self.db = db
        self.cost_service = CostService(db)

    async def chat(self, message: str, provider: str = "gemini", user_id: Optional[str] = None) -> dict:
        """Process a user message and return a response using the selected provider."""
        message_lower = message.lower().strip()
        provider_lower = provider.lower().strip()

        # Route to ChatGPT/OpenAI if requested
        if provider_lower in ["openai", "chatgpt"]:
            try:
                response = await self._chatgpt_response(message, user_id)
                return {
                    "response": response,
                    "source": "chatgpt",
                    "suggestions": self._get_suggestions(message_lower),
                }
            except Exception as e:
                logger.warning(f"OpenAI API call failed, falling back to rule-based KB: {e}")

        # Route to Gemini
        else:
            try:
                response = await self._gemini_response(message, user_id)
                return {
                    "response": response,
                    "source": "gemini_ai",
                    "suggestions": self._get_suggestions(message_lower),
                }
            except Exception as e:
                logger.warning(f"Gemini API call failed: {e}")
                # Try OpenAI as fallback before KB if key exists
                if settings.OPENAI_API_KEY:
                    try:
                        logger.info("Trying OpenAI API as fallback for Gemini")
                        response = await self._chatgpt_response(message, user_id)
                        return {
                            "response": response,
                            "source": "chatgpt",
                            "suggestions": self._get_suggestions(message_lower),
                        }
                    except Exception as ex:
                        logger.warning(f"OpenAI fallback call failed: {ex}")

        # Rule-based fallback if Gemini API call fails at runtime
        response = self._rule_based_response(message_lower, user_id)
        return {
            "response": response,
            "source": "knowledge_base",
            "suggestions": self._get_suggestions(message_lower),
        }

    def _get_active_anomalies(self, user_id: Optional[str]) -> list[Anomaly]:
        """Fetch unresolved anomalies from the database for the user."""
        if not user_id:
            return []
        try:
            return (
                self.db.query(Anomaly)
                .join(CostRecord, Anomaly.cost_record_id == CostRecord.id)
                .filter(CostRecord.user_id == user_id)
                .filter(Anomaly.is_resolved.is_(False))
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

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
            logger.error(f"Gemini API returned status {resp.status_code}: {resp.text}")
            raise Exception(f"Gemini API error (Status {resp.status_code})")

    async def _chatgpt_response(self, message: str, user_id: Optional[str] = None) -> str:
        """Generate response using OpenAI ChatGPT API."""
        if not settings.OPENAI_API_KEY:
            raise Exception("OpenAI API key is not configured.")

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

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            "temperature": 0.7
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "").strip()
            logger.error(f"OpenAI API returned status {resp.status_code}: {resp.text}")
            raise Exception(f"OpenAI API error (Status {resp.status_code})")

    async def chat_stream(
        self, message: str, provider: str = "gemini", user_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Stream chat responses from the chosen provider."""
        provider = provider.lower().strip()
        
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

        if provider in ["openai", "chatgpt"]:
            if not settings.OPENAI_API_KEY:
                fallback = self._rule_based_response(message.lower().strip(), user_id)
                for chunk in self._split_text_to_chunks(fallback):
                    yield json.dumps({"text": chunk, "source": "knowledge_base"})
                    await asyncio.sleep(0.01)
                return

            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": settings.OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                "stream": True,
                "temperature": 0.7
            }

            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    async with client.stream("POST", url, headers=headers, json=payload) as response:
                        if response.status_code != 200:
                            raise Exception(f"OpenAI error status: {response.status_code}")
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data_str = line[6:].strip()
                                if data_str == "[DONE]":
                                    break
                                try:
                                    data_json = json.loads(data_str)
                                    content = data_json["choices"][0]["delta"].get("content", "")
                                    if content:
                                        yield json.dumps({"text": content, "source": "chatgpt"})
                                except Exception:
                                    continue
                return
            except Exception as e:
                logger.warning(f"OpenAI stream failed: {e}")

        # Default Gemini streaming
        if provider == "gemini":
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
