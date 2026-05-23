"""
Pydantic schemas for API responses.
Define contracts for FastAPI endpoints.
"""

from typing import Optional, List, Any
from pydantic import BaseModel, Field


# ─── Analytics schemas ────────────────────────────────────────────────────────

class XGMatchEntry(BaseModel):
    """Per-match xG proxy entry."""

    match_id: int
    matchday: Optional[int] = None
    utc_date: Optional[str] = None
    status: Optional[str] = None
    home_team_id: Optional[int] = None
    home_team_name: str
    away_team_id: Optional[int] = None
    away_team_name: str
    home_xg: float
    away_xg: float
    home_goals: Optional[int] = None
    away_goals: Optional[int] = None

    class Config:
        populate_by_name = True


class XGResponse(BaseModel):
    """Response for GET /api/analytics/xg."""

    competition: str
    matchday: int
    method: str = "poisson_strength_proxy"
    note: str = (
        "xG estimated from season attack/defence indices. "
        "Not based on shot data (unavailable on free tier)."
    )
    matches: List[XGMatchEntry]

    class Config:
        populate_by_name = True


class FormEntry(BaseModel):
    """Per-team form entry."""

    team_id: int
    team_name: str
    form: str            # e.g. "WWDLW" — most recent last
    form_points: int
    matches_considered: int

    class Config:
        populate_by_name = True


class FormResponse(BaseModel):
    """Response for GET /api/analytics/standings-form."""

    competition: str
    last_n: int
    teams: List[FormEntry]

    class Config:
        populate_by_name = True


class ScorerEntry(BaseModel):
    """Individual scorer entry."""

    rank: int
    player_id: Optional[int] = None
    player_name: str
    team_id: Optional[int] = None
    team_name: str
    goals: int
    assists: Optional[int] = None
    penalties: Optional[int] = None
    played_matches: int
    goals_per_game: float

    class Config:
        populate_by_name = True


class TopScorersResponse(BaseModel):
    """Response for GET /api/analytics/top-scorers."""

    competition: str
    scorers: List[ScorerEntry]

    class Config:
        populate_by_name = True


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: str
    detail: Optional[str] = None
    status_code: int = Field(alias="statusCode")

    class Config:
        populate_by_name = True


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: str


class MatchResponse(BaseModel):
    """Simplified match response for API."""

    id: int
    utc_date: str = Field(alias="utcDate")
    status: str
    matchday: Optional[int] = None
    home_team_name: str = Field(alias="homeTeamName")
    home_team_id: int = Field(alias="homeTeamId")
    away_team_name: str = Field(alias="awayTeamName")
    away_team_id: int = Field(alias="awayTeamId")
    score: Optional[dict] = None

    class Config:
        populate_by_name = True


class MatchesListResponse(BaseModel):
    """Response for GET /api/matches."""

    count: int
    matches: List[MatchResponse]

    class Config:
        populate_by_name = True


class TeamStandingResponse(BaseModel):
    """Team entry in standings."""

    position: int
    team_name: str = Field(alias="teamName")
    team_id: int = Field(alias="teamId")
    played_games: int = Field(alias="playedGames")
    wins: int
    draws: int
    losses: int
    points: int
    goal_difference: int = Field(alias="goalDifference")

    class Config:
        populate_by_name = True


class StandingsResponse(BaseModel):
    """Response for GET /api/standings."""

    competition: str
    standings: List[TeamStandingResponse]

    class Config:
        populate_by_name = True


class TeamResponse(BaseModel):
    """Simplified team response."""

    id: int
    name: str
    short_name: Optional[str] = Field(None, alias="shortName")
    tla: Optional[str] = None
    founded: Optional[int] = None

    class Config:
        populate_by_name = True


class TeamsListResponse(BaseModel):
    """Response for GET /api/teams."""

    count: int
    competition: str
    teams: List[TeamResponse]

    class Config:
        populate_by_name = True
