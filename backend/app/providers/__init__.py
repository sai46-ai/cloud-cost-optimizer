"""
Multi-cloud Providers Package Factory
"""

from app.providers.base import BaseCloudProvider
from app.providers.aws import AWSCloudProvider
from app.providers.gcp import GCPCloudProvider
from app.providers.azure import AzureCloudProvider


def get_cloud_provider(name: str = "aws") -> BaseCloudProvider:
    """Factory function returning the specified cloud provider instance."""
    providers = {
        "aws": AWSCloudProvider(),
        "gcp": GCPCloudProvider(),
        "azure": AzureCloudProvider(),
    }
    return providers.get(name.lower(), AWSCloudProvider())
