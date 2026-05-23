/**
 * TypeScript interfaces matching FastAPI response schemas.
 *
 * Aliased fields (Pydantic Field(alias=...)) are serialised with the alias key
 * in JSON output. Snake_case fields without aliases stay snake_case.
 *
 * FastAPI endpoint → JSON key notes:
 *   /api/standings       → teamName, teamId, playedGames, goalDifference
 *   /api/matches         → utcDate, homeTeamName, homeTeamId, awayTeamName, awayTeamId
 *   /api/teams           → shortName
 *   /api/analytics/*     → snake_case (no aliases in those schemas)
 */

// ── Standings ────────────────────────────────────────────────────────────────

export interface TeamStanding {
  position: number;
  teamName: string;
  teamId: number;
  playedGames: number;
  wins: number;
  draws: number;
  losses: number;
  points: number;
  goalDifference: number;
}

export interface StandingsResponse {
  competition: string;
  standings: TeamStanding[];
}

// ── Matches ──────────────────────────────────────────────────────────────────

export interface MatchScore {
  winner: string | null;
  duration: string;
  fullTime: { home: number | null; away: number | null };
  halfTime: { home: number | null; away: number | null };
}

export interface Match {
  id: number;
  utcDate: string;
  status: string;
  matchday: number | null;
  homeTeamName: string;
  homeTeamId: number;
  awayTeamName: string;
  awayTeamId: number;
  score: MatchScore | null;
}

export interface MatchesResponse {
  count: number;
  matches: Match[];
}

// ── Teams ────────────────────────────────────────────────────────────────────

export interface Team {
  id: number;
  name: string;
  shortName: string | null;
  tla: string | null;
  founded: number | null;
}

export interface TeamsResponse {
  count: number;
  competition: string;
  teams: Team[];
}

// ── Analytics: xG ────────────────────────────────────────────────────────────

export interface XGMatchEntry {
  match_id: number;
  matchday: number | null;
  utc_date: string | null;
  status: string | null;
  home_team_id: number | null;
  home_team_name: string;
  away_team_id: number | null;
  away_team_name: string;
  home_xg: number;
  away_xg: number;
  home_goals: number | null;
  away_goals: number | null;
}

export interface XGResponse {
  competition: string;
  matchday: number;
  method: string;
  note: string;
  matches: XGMatchEntry[];
}

// ── Analytics: Form ───────────────────────────────────────────────────────────

export interface FormEntry {
  team_id: number;
  team_name: string;
  form: string;
  form_points: number;
  matches_considered: number;
}

export interface FormResponse {
  competition: string;
  last_n: number;
  teams: FormEntry[];
}

// ── Analytics: Top Scorers ────────────────────────────────────────────────────

export interface ScorerEntry {
  rank: number;
  player_id: number | null;
  player_name: string;
  team_id: number | null;
  team_name: string;
  goals: number;
  assists: number | null;
  penalties: number | null;
  played_matches: number;
  goals_per_game: number;
}

export interface TopScorersResponse {
  competition: string;
  scorers: ScorerEntry[];
}
