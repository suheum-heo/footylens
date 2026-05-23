"""
Matches endpoint router.
GET /api/matches?competition=PL&matchday=1
"""

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from logging import getLogger

from core.config import Settings, get_settings
from services.football_data_client import RateLimitedClient
from models.football_data import MatchesResponse
from schemas.responses import MatchesListResponse, MatchResponse, ErrorResponse

logger = getLogger(__name__)
router = APIRouter(prefix="/api", tags=["matches"])

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
    "/matches",
    response_model=MatchesListResponse,
    responses={400: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
)
async def get_matches(
    competition: str = Query(..., description="Competition code (PL, BL1, SA, PD, FL1)"),
    matchday: Optional[int] = Query(None, description="Specific matchday (optional)"),
    status: Optional[str] = Query(
        None,
        description="Filter by status (SCHEDULED, LIVE, IN_PLAY, PAUSED, FINISHED)",
    ),
    client: RateLimitedClient = Depends(get_client),
) -> MatchesListResponse:
    """
    Get matches for a competition.
    
    **Parameters:**
    - `competition`: Competition code (e.g., "PL" for Premier League, "BL1" for Bundesliga)
    - `matchday`: Optional specific matchday number
    - `status`: Optional filter by match status
    
    **Returns:** List of matches with basic info (teams, scores, status)
    """
    try:
        raw_response = await client.get_matches(
            competition=competition,
            matchday=matchday,
            status=status,
        )
        validated = MatchesResponse(**raw_response)

        # Transform to response schema
        matches = []
        for match in validated.matches:
            matches.append(
                MatchResponse(
                    id=match.id,
                    utc_date=match.utc_date.isoformat(),
                    status=match.status,
                    matchday=match.matchday,
                    home_team_name=match.home_team.name,
                    home_team_id=match.home_team.id,
                    away_team_name=match.away_team.name,
                    away_team_id=match.away_team.id,
                    score=match.score,
                )
            )

        return MatchesListResponse(count=len(matches), matches=matches)

    except ValueError as e:
        logger.error(f"Invalid competition or API error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        raise HTTPException(status_code=400, detail="Failed to fetch data from Football-Data.org")
    except Exception as e:
        logger.error(f"Unexpected error fetching matches: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
