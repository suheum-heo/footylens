"""
Teams endpoint router.
GET /api/teams?competition=PL
"""

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from logging import getLogger

from core.config import Settings, get_settings
from core.cache import get_cache
from services.football_data_client import RateLimitedClient
from models.football_data import TeamsResponse as TeamsModel
from schemas.responses import TeamsListResponse, TeamResponse, ErrorResponse

logger = getLogger(__name__)
router = APIRouter(prefix="/api", tags=["teams"])

# Lazy client initialization
_client: Optional[RateLimitedClient] = None


async def get_client(settings: Settings = Depends(get_settings)) -> RateLimitedClient:
    """Get or create rate-limited API client."""
    global _client
    if _client is None:
        _client = RateLimitedClient(
            api_key=settings.football_data_api_key,
            base_url=settings.football_data_base_url,
            rate_limit_requests=settings.rate_limit_requests,
            rate_limit_period_seconds=settings.rate_limit_period_seconds,
        )
    return _client


def _build_cache_key(competition: str) -> str:
    """Build cache key from parameters."""
    return f"teams:{competition}"


@router.get(
    "/teams",
    response_model=TeamsListResponse,
    responses={400: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
)
async def get_teams(
    competition: str = Query(..., description="Competition code (PL, BL1, SA, PD, FL1)"),
    client: RateLimitedClient = Depends(get_client),
) -> TeamsListResponse:
    """
    Get all teams in a competition.
    
    **Parameters:**
    - `competition`: Competition code (e.g., "PL" for Premier League)
    
    **Returns:** List of teams with basic info (name, founded, TLA code)
    
    **Caching:** Results are cached for 1 hour and served from cache on subsequent requests.
    """
    cache = get_cache()
    cache_key = _build_cache_key(competition)

    # Try to get from cache first
    cached_raw = cache.get(cache_key)
    if cached_raw is not None:
        logger.info(f"Serving teams from cache: {cache_key}")
        try:
            validated = TeamsModel(**cached_raw)
            teams = []
            for team in validated.teams:
                teams.append(
                    TeamResponse(
                        id=team.id,
                        name=team.name,
                        short_name=team.short_name,
                        tla=team.tla,
                        founded=team.founded,
                    )
                )
            return TeamsListResponse(
                count=len(teams),
                competition=competition,
                teams=teams,
            )
        except Exception as e:
            logger.error(f"Cache validation failed: {e}, fetching fresh")
            cache.clear(cache_key)

    # Cache miss or invalid, fetch fresh from API
    try:
        raw_response = await client.get_teams(competition=competition)
        validated = TeamsModel(**raw_response)

        # Update cache
        cache.set(cache_key, raw_response, ttl_minutes=60)
        logger.info(f"Cached teams: {cache_key}")

        teams = []
        for team in validated.teams:
            teams.append(
                TeamResponse(
                    id=team.id,
                    name=team.name,
                    short_name=team.short_name,
                    tla=team.tla,
                    founded=team.founded,
                )
            )

        return TeamsListResponse(
            count=len(teams),
            competition=competition,
            teams=teams,
        )

    except ValueError as e:
        logger.error(f"Invalid competition or API error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        raise HTTPException(status_code=400, detail="Failed to fetch data from Football-Data.org")
    except Exception as e:
        logger.error(f"Unexpected error fetching teams: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
