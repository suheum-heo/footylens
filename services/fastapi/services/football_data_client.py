"""
Football-Data.org API client with rate limiting.
Implements rate limiting (10 calls/min as per free tier) and retry logic.
"""

import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
import logging

logger = logging.getLogger(__name__)


class RateLimitedClient:
    """
    HTTP client for Football-Data.org API with rate limiting.
    
    Free tier: 10 calls/min
    Implements token bucket rate limiting to respect API constraints.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.football-data.org/v4",
        rate_limit_requests: int = 10,
        rate_limit_period_seconds: int = 60,
    ):
        """
        Initialize rate-limited API client.
        
        Args:
            api_key: Football-Data.org API key
            base_url: Base URL for API endpoints
            rate_limit_requests: Max requests per period (default 10 for free tier)
            rate_limit_period_seconds: Time window for rate limit (default 60s)
        """
        self.api_key = api_key
        self.base_url = base_url
        self.rate_limit_requests = rate_limit_requests
        self.rate_limit_period_seconds = rate_limit_period_seconds

        # Token bucket state
        self.tokens = rate_limit_requests
        self.last_refill = datetime.utcnow()
        self._lock = asyncio.Lock()

        # HTTP client headers
        self.headers = {
            "X-Auth-Token": api_key,
            "Accept": "application/json",
        }

    async def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time."""
        now = datetime.utcnow()
        elapsed = (now - self.last_refill).total_seconds()

        if elapsed >= self.rate_limit_period_seconds:
            self.tokens = self.rate_limit_requests
            self.last_refill = now
        else:
            # Proportional refill
            tokens_to_add = (
                elapsed / self.rate_limit_period_seconds
            ) * self.rate_limit_requests
            self.tokens = min(
                self.rate_limit_requests,
                self.tokens + tokens_to_add,
            )

    async def _wait_for_token(self) -> None:
        """Wait until a token is available, then consume it."""
        async with self._lock:
            await self._refill_tokens()

            if self.tokens < 1:
                # Calculate wait time
                wait_time = (
                    self.rate_limit_period_seconds
                    * (1 - self.tokens / self.rate_limit_requests)
                )
                logger.warning(
                    f"Rate limit reached. Waiting {wait_time:.2f}s before retry."
                )
                await asyncio.sleep(wait_time)
                await self._refill_tokens()

            self.tokens -= 1

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make a GET request to Football-Data.org API.
        
        Args:
            endpoint: API endpoint (e.g., "/matches", "/standings")
            params: Query parameters
        
        Returns:
            Parsed JSON response
        
        Raises:
            httpx.HTTPError: On HTTP errors
            ValueError: On invalid responses
        """
        await self._wait_for_token()

        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    logger.error("Rate limit exceeded by API")
                    raise ValueError("API rate limit exceeded") from e
                elif e.response.status_code == 404:
                    logger.error(f"Endpoint not found: {url}")
                    raise ValueError("Resource not found") from e
                else:
                    logger.error(f"HTTP error {e.response.status_code}: {e}")
                    raise
            except httpx.RequestError as e:
                logger.error(f"Request failed: {e}")
                raise

    async def get_matches(
        self,
        competition: str,
        matchday: Optional[int] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get matches for a competition.
        
        Args:
            competition: Competition code (e.g., "PL", "BL1", "SA", "PD", "FL1")
            matchday: Specific matchday (optional)
            status: Filter by status (SCHEDULED, LIVE, IN_PLAY, PAUSED, FINISHED)
        
        Returns:
            Matches data from API
        """
        params = {"competitions": competition}
        if matchday is not None:
            params["matchday"] = matchday
        if status:
            params["status"] = status

        return await self.get("/matches", params=params)

    async def get_standings(
        self,
        competition: str,
    ) -> Dict[str, Any]:
        """
        Get standings/league table for a competition.
        
        Args:
            competition: Competition code (e.g., "PL", "BL1", "SA", "PD", "FL1")
        
        Returns:
            Standings data from API
        """
        return await self.get(f"/competitions/{competition}/standings")

    async def get_teams(
        self,
        competition: str,
    ) -> Dict[str, Any]:
        """
        Get all teams in a competition.

        Args:
            competition: Competition code (e.g., "PL", "BL1", "SA", "PD", "FL1")

        Returns:
            Teams data from API
        """
        return await self.get(f"/competitions/{competition}/teams")

    async def get_competition_matches(
        self,
        competition: str,
        matchday: Optional[int] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get matches via the competition-specific endpoint.

        Unlike get_matches() (which defaults to today's date window),
        this returns ALL matches for the current season and is the correct
        endpoint for analytics that need full-season match history.

        Args:
            competition: Competition code (e.g., "PL")
            matchday: Specific matchday (optional)
            status: Filter by status e.g. "FINISHED" (optional)

        Returns:
            Matches data from API
        """
        params: Dict[str, Any] = {}
        if matchday is not None:
            params["matchday"] = matchday
        if status:
            params["status"] = status
        return await self.get(
            f"/competitions/{competition}/matches",
            params=params if params else None,
        )

    async def get_scorers(
        self,
        competition: str,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Get top scorers for a competition.

        Args:
            competition: Competition code (e.g., "PL")
            limit: Max scorers to return (free tier may cap at 10)

        Returns:
            Scorers data from API
        """
        return await self.get(
            f"/competitions/{competition}/scorers",
            params={"limit": limit},
        )
