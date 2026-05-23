"""
Analytics endpoints.

GET /api/analytics/xg?competition=PL&matchday=38
GET /api/analytics/standings-form?competition=PL&last_n=5
GET /api/analytics/top-scorers?competition=PL

All results are cached for 24 hours — analytics don't change after a matchday
completes and computing them on every request wastes the free-tier rate limit.

Cache keys:
    analytics:xg:{competition}:{matchday}
    analytics:form:{competition}:{last_n}
    analytics:scorers:{competition}

Data flow for each endpoint:
    xG      → standings (cached 1h) + matchday matches (cached 1h) → compute
    form    → all FINISHED matches (cached 24h) → compute
    scorers → /scorers API call (cached 24h) → compute
"""

import asyncio
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from logging import getLogger

from core.cache import get_cache
from services.client_factory import get_client
from services.football_data_client import RateLimitedClient
from services.analytics_engine import compute_xg_proxy, compute_form, compute_top_scorers
from schemas.responses import (
    XGResponse, XGMatchEntry,
    FormResponse, FormEntry,
    TopScorersResponse, ScorerEntry,
    ErrorResponse,
)

logger = getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["analytics"])

_ANALYTICS_TTL = 24 * 60  # 24 hours in minutes


# ─── xG endpoint ──────────────────────────────────────────────────────────────

@router.get(
    "/xg",
    response_model=XGResponse,
    responses={400: {"model": ErrorResponse}},
)
async def get_xg(
    competition: str = Query(..., description="Competition code (PL, BL1, SA, PD, FL1)"),
    matchday: int = Query(..., ge=1, le=38, description="Matchday number (1–38)"),
    client: RateLimitedClient = Depends(get_client),
) -> XGResponse:
    """
    xG proxy for a specific matchday, computed from team season attack/defence strengths.

    **Method:** Simplified Poisson strength model —
    `xg_team = attack_index × opponent_defence_index × league_avg_goals`

    where indices are derived from each team's `goalsFor / goalsAgainst / playedGames`
    in the current standings. Not based on shot data (unavailable on free tier).

    **Caching:** Cached 24 hours.
    """
    cache = get_cache()
    cache_key = f"analytics:xg:{competition.upper()}:{matchday}"

    cached = cache.get(cache_key)
    if cached is not None:
        logger.info(f"Cache hit: {cache_key}")
        return XGResponse(**cached)

    try:
        # standings:{comp} is shared with the standings router — cache hit is likely.
        standings_key = f"standings:{competition.upper()}"
        matches_key = f"analytics:raw_matches:{competition.upper()}:{matchday}"

        raw_standings = cache.get(standings_key)
        raw_matches_data = cache.get(matches_key)

        if raw_standings is None and raw_matches_data is None:
            raw_standings, raw_matches_data = await asyncio.gather(
                client.get_standings(competition=competition),
                client.get_competition_matches(competition=competition, matchday=matchday),
            )
            cache.set(standings_key, raw_standings, ttl_minutes=60)
            cache.set(matches_key, raw_matches_data, ttl_minutes=60)
        elif raw_standings is None:
            raw_standings = await client.get_standings(competition=competition)
            cache.set(standings_key, raw_standings, ttl_minutes=60)
        elif raw_matches_data is None:
            raw_matches_data = await client.get_competition_matches(
                competition=competition, matchday=matchday
            )
            cache.set(matches_key, raw_matches_data, ttl_minutes=60)

        standings_list = raw_standings.get("standings", [])
        standings_list = raw_standings.get("standings", [])
        total_table = next(
            (s["table"] for s in standings_list if s.get("type") == "TOTAL"),
            standings_list[0]["table"] if standings_list else [],
        )

        raw_matches = raw_matches_data.get("matches", [])
        if not raw_matches:
            return XGResponse(competition=competition, matchday=matchday, matches=[])

        xg_data = compute_xg_proxy(raw_matches, total_table)

        result = XGResponse(
            competition=competition.upper(),
            matchday=matchday,
            matches=[XGMatchEntry(**m) for m in xg_data],
        )
        cache.set(cache_key, result.model_dump(), ttl_minutes=_ANALYTICS_TTL)
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.HTTPError as e:
        logger.error(f"HTTP error in xG endpoint: {e}")
        raise HTTPException(status_code=400, detail="Failed to fetch data from Football-Data.org")
    except Exception as e:
        logger.error(f"xG computation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Analytics computation failed")


# ─── Form endpoint ────────────────────────────────────────────────────────────

@router.get(
    "/standings-form",
    response_model=FormResponse,
    responses={400: {"model": ErrorResponse}},
)
async def get_standings_form(
    competition: str = Query(..., description="Competition code (PL, BL1, SA, PD, FL1)"),
    last_n: int = Query(5, ge=1, le=10, description="Number of recent matches to consider"),
    client: RateLimitedClient = Depends(get_client),
) -> FormResponse:
    """
    Last-N form for every team in the competition.

    Returns a form string (e.g. `WWDLW`, most recent last), total points from
    those N matches, and how many finished matches were available.

    **Caching:** Cached 24 hours.
    """
    cache = get_cache()
    cache_key = f"analytics:form:{competition.upper()}:{last_n}"

    cached = cache.get(cache_key)
    if cached is not None:
        logger.info(f"Cache hit: {cache_key}")
        return FormResponse(**cached)

    try:
        # All FINISHED matches — cached under a shared key regardless of last_n
        # so multiple last_n values share the same expensive API call.
        raw_matches_key = f"analytics:raw_matches_finished:{competition.upper()}"
        raw_data = cache.get(raw_matches_key)

        if raw_data is None:
            raw_data = await client.get_competition_matches(
                competition=competition, status="FINISHED"
            )
            cache.set(raw_matches_key, raw_data, ttl_minutes=_ANALYTICS_TTL)

        raw_matches = raw_data.get("matches", [])
        form_data = compute_form(raw_matches, last_n=last_n)

        result = FormResponse(
            competition=competition.upper(),
            last_n=last_n,
            teams=[FormEntry(**t) for t in form_data],
        )
        cache.set(cache_key, result.model_dump(), ttl_minutes=_ANALYTICS_TTL)
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.HTTPError as e:
        logger.error(f"HTTP error in form endpoint: {e}")
        raise HTTPException(status_code=400, detail="Failed to fetch data from Football-Data.org")
    except Exception as e:
        logger.error(f"Form computation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Analytics computation failed")


# ─── Top scorers endpoint ─────────────────────────────────────────────────────

@router.get(
    "/top-scorers",
    response_model=TopScorersResponse,
    responses={400: {"model": ErrorResponse}},
)
async def get_top_scorers(
    competition: str = Query(..., description="Competition code (PL, BL1, SA, PD, FL1)"),
    limit: int = Query(20, ge=1, le=50, description="Max scorers to return"),
    client: RateLimitedClient = Depends(get_client),
) -> TopScorersResponse:
    """
    Top scorers for the competition, ranked by goals then assists.
    Includes goals-per-game rate.

    **Caching:** Cached 24 hours.
    """
    cache = get_cache()
    cache_key = f"analytics:scorers:{competition.upper()}:{limit}"

    cached = cache.get(cache_key)
    if cached is not None:
        logger.info(f"Cache hit: {cache_key}")
        return TopScorersResponse(**cached)

    try:
        raw_data = await client.get_scorers(competition=competition, limit=limit)
        raw_scorers = raw_data.get("scorers", [])

        scorer_data = compute_top_scorers(raw_scorers, limit=limit)
        result = TopScorersResponse(
            competition=competition.upper(),
            scorers=[ScorerEntry(**s) for s in scorer_data],
        )
        cache.set(cache_key, result.model_dump(), ttl_minutes=_ANALYTICS_TTL)
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.HTTPError as e:
        logger.error(f"HTTP error in top-scorers endpoint: {e}")
        raise HTTPException(status_code=400, detail="Failed to fetch data from Football-Data.org")
    except Exception as e:
        logger.error(f"Scorers computation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Analytics computation failed")
