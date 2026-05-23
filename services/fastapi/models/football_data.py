"""
Data models for Football-Data.org API responses.
Used for validation at the service boundary.
"""

from typing import Optional, List, Any
from pydantic import BaseModel, Field
from datetime import datetime


class TeamData(BaseModel):
    """Team information from Football-Data.org."""

    id: int
    name: str
    short_name: Optional[str] = Field(None, alias="shortName")
    tla: Optional[str] = None  # Three-letter code
    founded: Optional[int] = None
    area: Optional[Any] = None  # API returns nested object {"id", "name", "code", ...}

    class Config:
        populate_by_name = True


class CompetitionData(BaseModel):
    """Competition/League information."""

    id: int
    name: str
    code: str
    area: Optional[Any] = None  # API returns nested object {"id", "name", "code", ...}

    class Config:
        populate_by_name = True


class MatchData(BaseModel):
    """Individual match information."""

    id: int
    utc_date: datetime = Field(alias="utcDate")
    status: str  # SCHEDULED, LIVE, IN_PLAY, PAUSED, FINISHED
    matchday: Optional[int] = None
    stage: Optional[str] = None
    home_team: TeamData = Field(alias="homeTeam")
    away_team: TeamData = Field(alias="awayTeam")
    score: Optional[dict] = None
    odds: Optional[dict] = None
    referee: Optional[dict] = None

    class Config:
        populate_by_name = True


class MatchesResponse(BaseModel):
    """Response for /matches endpoint."""

    filters: Optional[dict] = None
    result_set: Optional[dict] = Field(None, alias="resultSet")
    matches: List[MatchData]

    class Config:
        populate_by_name = True


class StandingsTableEntry(BaseModel):
    """League table entry. API returns won/draw/lost; we map to wins/draws/losses."""

    position: int
    team: TeamData
    played_games: int = Field(alias="playedGames")
    wins: int = Field(alias="won")
    draws: int = Field(alias="draw")
    losses: int = Field(alias="lost")
    points: int
    goals_for: int = Field(alias="goalsFor")
    goals_against: int = Field(alias="goalsAgainst")
    goal_difference: int = Field(alias="goalDifference")

    class Config:
        populate_by_name = True


class StandingsTable(BaseModel):
    """League standings table. The API omits 'name'; type/stage/group identify it."""

    type: str
    stage: Optional[str] = None
    group: Optional[str] = None
    table: List[StandingsTableEntry]

    class Config:
        populate_by_name = True


class StandingsResponse(BaseModel):
    """Response for /standings endpoint."""

    filters: Optional[dict] = None
    competition: CompetitionData
    season: Optional[dict] = None
    standings: List[StandingsTable] = []

    class Config:
        populate_by_name = True


class TeamsResponse(BaseModel):
    """Response for /teams endpoint."""

    filters: Optional[dict] = None
    competition: CompetitionData
    season: Optional[dict] = None
    teams: List[TeamData]

    class Config:
        populate_by_name = True
