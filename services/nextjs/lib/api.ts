/**
 * Typed fetch helpers for the FootyLens FastAPI service.
 * All requests are server-side only (called from Server Components).
 * Data is revalidated every hour; FastAPI's own in-memory cache handles
 * upstream rate limits.
 */

import type {
  StandingsResponse,
  MatchesResponse,
  XGResponse,
  FormResponse,
  TopScorersResponse,
} from "@/types/api";

const BASE_URL = process.env.FASTAPI_URL ?? "http://localhost:8000";
const REVALIDATE = 3600; // 1 hour

async function apiFetch<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      next: { revalidate: REVALIDATE },
    });
    if (!res.ok) return null;
    return res.json() as Promise<T>;
  } catch {
    return null;
  }
}

export function getStandings(competition = "PL"): Promise<StandingsResponse | null> {
  return apiFetch<StandingsResponse>(`/api/standings?competition=${competition}`);
}

export function getMatches(
  competition = "PL",
  matchday?: number
): Promise<MatchesResponse | null> {
  const params = new URLSearchParams({ competition });
  if (matchday != null) params.set("matchday", String(matchday));
  return apiFetch<MatchesResponse>(`/api/matches?${params}`);
}

export function getXG(
  competition = "PL",
  matchday = 38
): Promise<XGResponse | null> {
  return apiFetch<XGResponse>(
    `/api/analytics/xg?competition=${competition}&matchday=${matchday}`
  );
}

export function getForm(
  competition = "PL",
  lastN = 5
): Promise<FormResponse | null> {
  return apiFetch<FormResponse>(
    `/api/analytics/standings-form?competition=${competition}&last_n=${lastN}`
  );
}

export function getTopScorers(
  competition = "PL",
  limit = 20
): Promise<TopScorersResponse | null> {
  return apiFetch<TopScorersResponse>(
    `/api/analytics/top-scorers?competition=${competition}&limit=${limit}`
  );
}
