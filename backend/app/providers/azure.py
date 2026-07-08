"""
Microsoft Azure Provider Implementation (Modular Interface)
"""

from typing import Dict, List, Any
from datetime import date
from app.providers.base import BaseCloudProvider


class AzureCloudProvider(BaseCloudProvider):
    @property
    def provider_name(self) -> str:
        return "azure"

    def is_configured(self) -> bool:
        return False

    async def get_cost_data(
        self, start_date: date, end_date: date, granularity: str = "DAILY"
    ) -> List[Dict[str, Any]]:
        return []

    async def get_inventory(self) -> List[Dict[str, Any]]:
        return []

    async def get_rightsizing_recommendations(self) -> List[Dict[str, Any]]:
        return []
