"""
Standings endpoint router.
GET /api/standings?competition=PL
"""

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from logging import getLogger

from core.cache import get_cache
from services.client_factory import get_client
from services.football_data_client import RateLimitedClient
from models.football_data import StandingsResponse as StandingsModel
from schemas.responses import StandingsResponse, TeamStandingResponse, ErrorResponse

logger = getLogger(__name__)
router = APIRouter(prefix="/api", tags=["standings"])


def _build_cache_key(competition: str) -> str:
    """Build cache key from parameters."""
    return f"standings:{competition}"


@router.get(
    "/standings",
    response_model=StandingsResponse,
    responses={400: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
)
async def get_standings(
    competition: str = Query(..., description="Competition code (PL, BL1, SA, PD, FL1)"),
    client: RateLimitedClient = Depends(get_client),
) -> StandingsResponse:
    """
    Get league standings/table for a competition.
    
    **Parameters:**
    - `competition`: Competition code (e.g., "PL" for Premier League)
    
    **Returns:** League table with team positions, points, and record
    
    **Caching:** Results are cached for 1 hour and served from cache on subsequent requests.
    """
    cache = get_cache()
    cache_key = _build_cache_key(competition)

    # Try to get from cache first
    cached_raw = cache.get(cache_key)
    if cached_raw is not None:
        logger.info(f"Serving standings from cache: {cache_key}")
        try:
            validated = StandingsModel(**cached_raw)
            standings = []
            if validated.standings:
                table = validated.standings[0].table
                for entry in table:
                    standings.append(
                        TeamStandingResponse(
                            position=entry.position,
                            team_name=entry.team.name,
                            team_id=entry.team.id,
                            played_games=entry.played_games,
                            wins=entry.wins,
                            draws=entry.draws,
                            losses=entry.losses,
                            points=entry.points,
                            goal_difference=entry.goal_difference,
                        )
                    )
            return StandingsResponse(competition=competition, standings=standings)
        except Exception as e:
            logger.error(f"Cache validation failed: {e}, fetching fresh")
            cache.clear(cache_key)

    # Cache miss or invalid, fetch fresh from API
    try:
        raw_response = await client.get_standings(competition=competition)
        
        # Validate basic structure
        if not raw_response or "standings" not in raw_response:
            raise ValueError("Invalid standings response structure")
        
        standings_list = raw_response.get("standings", [])
        if not standings_list or not isinstance(standings_list, list) or len(standings_list) == 0:
            logger.warning(f"No standings data for {competition}")
            return StandingsResponse(competition=competition, standings=[])

        # Extract first standings table (usually overall)
        standings_data = standings_list[0]
        if "table" not in standings_data or not standings_data["table"]:
            logger.warning(f"No table in standings data for {competition}")
            return StandingsResponse(competition=competition, standings=[])

        # Update cache
        cache.set(cache_key, raw_response, ttl_minutes=60)
        logger.info(f"Cached standings: {cache_key}")

        # Transform table to response schema
        standings = []
        for entry in standings_data["table"]:
            standings.append(
                TeamStandingResponse(
                    position=entry.get("position", 0),
                    team_name=entry.get("team", {}).get("name", "Unknown"),
                    team_id=entry.get("team", {}).get("id", 0),
                    played_games=entry.get("playedGames", 0),
                    wins=entry.get("won", 0),
                    draws=entry.get("draw", 0),
                    losses=entry.get("lost", 0),
                    points=entry.get("points", 0),
                    goal_difference=entry.get("goalDifference", 0),
                )
            )

        return StandingsResponse(competition=competition, standings=standings)

    except ValueError as e:
        logger.error(f"Invalid competition or API error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        raise HTTPException(status_code=400, detail="Failed to fetch data from Football-Data.org")
    except Exception as e:
        logger.error(f"Unexpected error fetching standings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
