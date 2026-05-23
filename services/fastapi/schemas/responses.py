"""
Pydantic schemas for API responses.
Define contracts for FastAPI endpoints.
"""

from typing import Optional, List, Any
from pydantic import BaseModel, Field


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
