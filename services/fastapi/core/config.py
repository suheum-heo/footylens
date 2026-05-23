"""
FastAPI core configuration.
Loads environment variables and provides app-wide settings.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


# Find .env file in project root (two levels up from this file)
project_root = Path(__file__).parent.parent.parent.parent
env_file = project_root / ".env"


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    # Football-Data.org API
    football_data_api_key: str
    football_data_base_url: str = "https://api.football-data.org/v4"

    # Rate limiting (Football-Data.org free tier: 10 calls/min)
    rate_limit_requests: int = 10
    rate_limit_period_seconds: int = 60

    # FastAPI
    fastapi_debug: bool = True
    fastapi_host: str = "0.0.0.0"
    fastapi_port: int = 8000

    class Config:
        env_file = str(env_file)
        case_sensitive = False


def get_settings() -> Settings:
    """Get application settings (used as FastAPI dependency)."""
    return Settings()
