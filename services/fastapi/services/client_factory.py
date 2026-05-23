"""
Shared RateLimitedClient factory for FastAPI routers.

All four routers (matches, standings, teams, analytics) need the same
client instance. Centralising the factory here avoids copy-pasting the
same 10-line get_client() dependency function into every router.
"""

from typing import Optional
from fastapi import Depends

from core.config import Settings, get_settings
from services.football_data_client import RateLimitedClient

_client: Optional[RateLimitedClient] = None


async def get_client(settings: Settings = Depends(get_settings)) -> RateLimitedClient:
    """FastAPI dependency: return (or lazily create) the shared rate-limited API client."""
    global _client
    if _client is None:
        _client = RateLimitedClient(
            api_key=settings.football_data_api_key,
            base_url=settings.football_data_base_url,
            rate_limit_requests=settings.rate_limit_requests,
            rate_limit_period_seconds=settings.rate_limit_period_seconds,
        )
    return _client
