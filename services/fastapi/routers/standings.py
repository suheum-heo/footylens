"""
Standings endpoint router.
GET /api/standings?competition=PL
"""

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from logging import getLogger

from core.config import Settings, get_settings
from services.football_data_client import RateLimitedClient
from models.football_data import StandingsResponse as StandingsModel
from schemas.responses import StandingsResponse, TeamStandingResponse, ErrorResponse

logger = getLogger(__name__)
router = APIRouter(prefix="/api", tags=["standings"])

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
    """
    try:
        raw_response = await client.get_standings(competition=competition)
        validated = StandingsModel(**raw_response)

        # Transform to response schema (use first standings table, usually overall)
        standings = []
        if validated.standings:
            table = validated.standings[0].standings
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

    except ValueError as e:
        logger.error(f"Invalid competition or API error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        raise HTTPException(status_code=400, detail="Failed to fetch data from Football-Data.org")
    except Exception as e:
        logger.error(f"Unexpected error fetching standings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
