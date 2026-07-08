"""
Multi-Cloud Provider Abstraction Interface
Defines standard contracts for AWS, GCP, Azure, and future cloud providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import date


class BaseCloudProvider(ABC):
    """Abstract base class for cloud cost and inventory providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the cloud provider (e.g. aws, gcp, azure)."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider credentials/session are valid."""
        pass

    @abstractmethod
    async def get_cost_data(
        self, start_date: date, end_date: date, granularity: str = "DAILY"
    ) -> List[Dict[str, Any]]:
        """Fetch historical cost and usage records."""
        pass

    @abstractmethod
    async def get_inventory(self) -> List[Dict[str, Any]]:
        """Fetch list of active cloud resources across compute, storage, DB."""
        pass

    @abstractmethod
    async def get_rightsizing_recommendations(self) -> List[Dict[str, Any]]:
        """Fetch cost optimization recommendations (e.g. idle compute, lifecycle policies)."""
        pass
