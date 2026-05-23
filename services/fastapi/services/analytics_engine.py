"""
Analytics engine for FootyLens.

All functions are pure/synchronous — they take raw API dicts and return
computed results. Keeping them sync makes testing trivial and avoids
event-loop complications with pandas/numpy.

xG Proxy methodology
--------------------
Football-Data.org free tier has no shot data, so we use a simplified
Poisson attack/defence strength model (a well-known proxy technique):

    xg_home = α_home × β_away × λ_avg
    xg_away = α_away × β_home × λ_avg

where:
    α_i  = team i goals_per_game / league_avg_goals_per_game   (attack index)
    β_i  = team i conceded_per_game / league_avg_goals_per_game (defence index)
    λ_avg = league average goals per team per game

This is transparent and interpretable: a value > goals_scored means the
team underperformed their average, < means they overperformed.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ─── xG Proxy ─────────────────────────────────────────────────────────────────

def compute_xg_proxy(
    matches: list[dict[str, Any]],
    standings_table: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Estimate per-match xG proxy for the given matchday.

    Args:
        matches: Raw match dicts from Football-Data.org (one matchday).
        standings_table: The 'table' array from the TOTAL standings entry.
                         Each row has: team.id, goalsFor, goalsAgainst, playedGames.

    Returns:
        List of dicts, one per match, containing xG estimates and actual goals.
    """
    if not standings_table:
        logger.warning("Empty standings table — cannot compute xG proxy")
        return []

    # ── Build team strength lookup from standings ─────────────────────────
    rows = []
    for entry in standings_table:
        team = entry.get("team", {})
        played = entry.get("playedGames", 1) or 1  # guard div-by-zero
        rows.append({
            "team_id": team.get("id"),
            "team_name": team.get("name", ""),
            "goals_for": entry.get("goalsFor", 0),
            "goals_against": entry.get("goalsAgainst", 0),
            "played": played,
        })

    df = pd.DataFrame(rows)
    df["goals_per_game"] = df["goals_for"] / df["played"]
    df["conceded_per_game"] = df["goals_against"] / df["played"]

    league_avg = float(df["goals_per_game"].mean())
    if league_avg == 0:
        league_avg = 1.0  # fallback to avoid division by zero

    # Attack/defence indices relative to league average
    df["attack_idx"] = df["goals_per_game"] / league_avg
    df["defence_idx"] = df["conceded_per_game"] / league_avg

    team_stats: dict[int, dict] = (
        df.set_index("team_id")[["attack_idx", "defence_idx", "team_name"]]
        .to_dict("index")
    )

    # ── Compute per-match xG ──────────────────────────────────────────────
    results = []
    for m in matches:
        home_data = m.get("homeTeam", {})
        away_data = m.get("awayTeam", {})
        home_id = home_data.get("id")
        away_id = away_data.get("id")

        h_stats = team_stats.get(home_id, {"attack_idx": 1.0, "defence_idx": 1.0})
        a_stats = team_stats.get(away_id, {"attack_idx": 1.0, "defence_idx": 1.0})

        # xg = attack_strength × opponent_defence_weakness × league_average
        xg_home = float(np.clip(
            h_stats["attack_idx"] * a_stats["defence_idx"] * league_avg,
            0.0, 10.0,
        ))
        xg_away = float(np.clip(
            a_stats["attack_idx"] * h_stats["defence_idx"] * league_avg,
            0.0, 10.0,
        ))

        score = m.get("score", {})
        ft = score.get("fullTime", {}) or {}

        results.append({
            "match_id": m.get("id"),
            "matchday": m.get("matchday"),
            "utc_date": m.get("utcDate"),
            "status": m.get("status"),
            "home_team_id": home_id,
            "home_team_name": home_data.get("name", ""),
            "away_team_id": away_id,
            "away_team_name": away_data.get("name", ""),
            "home_xg": round(xg_home, 2),
            "away_xg": round(xg_away, 2),
            "home_goals": ft.get("home"),
            "away_goals": ft.get("away"),
        })

    return results


# ─── Form calculator ──────────────────────────────────────────────────────────

def compute_form(
    all_matches: list[dict[str, Any]],
    last_n: int = 5,
) -> list[dict[str, Any]]:
    """
    Compute last-N form string and points for every team.

    Args:
        all_matches: All FINISHED match dicts for the competition.
        last_n: Number of most-recent results to consider (default 5).

    Returns:
        List of dicts sorted by form_points desc, then total_points asc (as tiebreak).
        Each dict: team_id, team_name, form (e.g. "WWDLW"), form_points, matches_considered.
    """
    finished = [
        m for m in all_matches
        if m.get("status") == "FINISHED"
        and m.get("score", {}).get("fullTime")
    ]
    if not finished:
        return []

    # Flatten into per-team result rows
    rows = []
    for m in finished:
        utc = m.get("utcDate", "")
        ft = m.get("score", {}).get("fullTime", {}) or {}
        home_g = ft.get("home")
        away_g = ft.get("away")
        if home_g is None or away_g is None:
            continue

        matchday = m.get("matchday", 0)
        home = m.get("homeTeam", {})
        away = m.get("awayTeam", {})

        # Home perspective
        if home.get("id"):
            result = "W" if home_g > away_g else ("D" if home_g == away_g else "L")
            rows.append({
                "team_id": home["id"],
                "team_name": home.get("name", ""),
                "utc_date": utc,
                "matchday": matchday,
                "result": result,
            })

        # Away perspective
        if away.get("id"):
            result = "W" if away_g > home_g else ("D" if home_g == away_g else "L")
            rows.append({
                "team_id": away["id"],
                "team_name": away.get("name", ""),
                "utc_date": utc,
                "matchday": matchday,
                "result": result,
            })

    if not rows:
        return []

    df = pd.DataFrame(rows)
    df["utc_date"] = pd.to_datetime(df["utc_date"], utc=True, errors="coerce")
    df = df.sort_values(["team_id", "utc_date"])

    POINTS = {"W": 3, "D": 1, "L": 0}

    output = []
    for team_id, grp in df.groupby("team_id"):
        recent = grp.tail(last_n)
        form_str = "".join(recent["result"].tolist())
        form_pts = int(recent["result"].map(POINTS).sum())
        team_name = grp["team_name"].iloc[-1]
        output.append({
            "team_id": int(team_id),
            "team_name": team_name,
            "form": form_str,
            "form_points": form_pts,
            "matches_considered": len(recent),
        })

    # Sort: best form first (by points desc, then alphabetical as stable tiebreak)
    output.sort(key=lambda x: (-x["form_points"], x["team_name"]))
    return output


# ─── Top scorers ──────────────────────────────────────────────────────────────

def compute_top_scorers(
    scorers: list[dict[str, Any]],
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Rank top scorers and enrich with goals-per-game.

    Args:
        scorers: Raw scorer dicts from Football-Data.org /scorers endpoint.
        limit: Max entries to return.

    Returns:
        List of scorer dicts sorted by goals desc, assists desc.
    """
    if not scorers:
        return []

    rows = []
    for s in scorers:
        player = s.get("player", {})
        team = s.get("team", {})
        played = s.get("playedMatches") or 1
        goals = s.get("goals") or 0
        rows.append({
            "player_id": player.get("id"),
            "player_name": player.get("name", ""),
            "team_id": team.get("id"),
            "team_name": team.get("name", ""),
            "goals": goals,
            "assists": s.get("assists"),
            "penalties": s.get("penalties"),
            "played_matches": played,
            "goals_per_game": round(goals / played, 2),
        })

    if not rows:
        return []

    df = pd.DataFrame(rows)
    df = df.sort_values(
        ["goals", "assists"],
        ascending=[False, False],
        na_position="last",
    ).head(limit).reset_index(drop=True)

    df.insert(0, "rank", df.index + 1)
    records = df.to_dict("records")
    # Pandas uses float NaN for missing int/nullable fields; replace with None
    # so Pydantic serialises them as JSON null rather than raising a validation error.
    return [
        {k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in row.items()}
        for row in records
    ]
