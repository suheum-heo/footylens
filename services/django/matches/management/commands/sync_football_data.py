"""
Management command: sync_football_data

Pulls data from Football-Data.org and upserts it into the Django DB.
All operations are idempotent — safe to run repeatedly.

Usage:
  python manage.py sync_football_data --competition PL
  python manage.py sync_football_data --competition PL --matchday 38
  python manage.py sync_football_data --competition PL --full

Sync order (FK dependency chain):
  1. Competition  (no deps)
  2. Teams + Players  (no deps)
  3. Standings + TableEntries  (requires Competition + Teams)
  4. Matches  (requires Competition + Teams)

Rate limiting:
  Free tier is 10 calls/min. We make ≤4 calls per run and sleep
  CALL_SLEEP seconds between each to stay well below the limit.
"""

import time
import logging
from datetime import date, datetime, timezone
from typing import Any, Optional

import httpx
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from matches.models import Competition, Match
from teams.models import Player, Team
from standings.models import Standing, TableEntry

logger = logging.getLogger(__name__)

# Sleep between API calls to respect the 10 calls/min free-tier limit.
# 7 s ≈ 8.5 calls/min — comfortable margin.
CALL_SLEEP = 7


# ─── HTTP client ──────────────────────────────────────────────────────────────

class FootballDataClient:
    """
    Thin synchronous httpx wrapper for Football-Data.org v4.
    Raises CommandError on 4xx/5xx so the caller gets a clean message.
    """

    def __init__(self, api_key: str, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = {
            "X-Auth-Token": api_key,
            "Accept": "application/json",
        }

    def get(self, path: str, params: Optional[dict] = None) -> dict:
        url = f"{self._base_url}{path}"
        try:
            resp = httpx.get(url, headers=self._headers, params=params, timeout=15.0)
        except httpx.RequestError as exc:
            raise CommandError(f"Network error fetching {url}: {exc}") from exc

        if resp.status_code == 429:
            raise CommandError(
                "Football-Data.org rate limit exceeded. "
                "Wait 60 s and retry, or reduce call frequency."
            )
        if resp.status_code == 404:
            raise CommandError(f"Resource not found: {url}")
        if resp.status_code >= 400:
            raise CommandError(
                f"API error {resp.status_code} for {url}: {resp.text[:200]}"
            )

        return resp.json()


# ─── Parsing helpers ──────────────────────────────────────────────────────────

def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    """Parse ISO-8601 datetime string → aware datetime. Returns None if blank."""
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _parse_date(value: Optional[str]) -> Optional[date]:
    """Parse YYYY-MM-DD string → date. Returns None if blank."""
    if not value:
        return None
    return date.fromisoformat(value)


def _area(obj: dict) -> tuple[str, str]:
    """Extract (area_name, area_code) from an API object's 'area' field."""
    area = obj.get("area") or {}
    if isinstance(area, dict):
        return area.get("name", ""), area.get("code", "")
    return "", ""


# ─── Sync steps ───────────────────────────────────────────────────────────────

def sync_competition(client: FootballDataClient, code: str) -> Competition:
    """
    Fetch /competitions/{code} and upsert the Competition row.
    Returns the Competition instance.
    """
    data = client.get(f"/competitions/{code}")

    area_name, area_code = _area(data)
    competition, created = Competition.objects.update_or_create(
        id=data["id"],
        defaults={
            "name": data["name"],
            "code": data["code"],
            "area_name": area_name,
            "area_code": area_code,
            "emblem_url": data.get("emblem") or "",
        },
    )
    action = "Created" if created else "Updated"
    logger.info(f"{action} competition: {competition}")
    return competition


def sync_teams(
    client: FootballDataClient,
    competition: Competition,
    sync_players: bool = False,
) -> list[Team]:
    """
    Fetch /competitions/{code}/teams and upsert Team rows.
    If sync_players=True, also upsert Player rows for each team's squad,
    deleting anyone no longer in the squad.
    Returns the list of upserted Teams.
    """
    data = client.get(f"/competitions/{competition.code}/teams")
    raw_teams = data.get("teams", [])

    teams: list[Team] = []
    for t in raw_teams:
        area_name, area_code = _area(t)
        team, created = Team.objects.update_or_create(
            id=t["id"],
            defaults={
                "name": t.get("name", ""),
                "short_name": t.get("shortName") or "",
                "tla": t.get("tla") or "",
                "founded": t.get("founded"),
                "crest_url": t.get("crest") or "",
                "venue": t.get("venue") or "",
                "area_name": area_name,
                "area_code": area_code,
            },
        )
        teams.append(team)
        action = "Created" if created else "Updated"
        logger.info(f"  {action} team: {team.name}")

        if sync_players:
            _upsert_squad(team, t.get("squad", []))

    return teams


def _upsert_squad(team: Team, squad: list[dict]) -> None:
    """
    Replace a team's player roster with the current squad data.
    Deletes players no longer in the squad; upserts those present.
    """
    incoming_ids = set()
    valid_positions = {c[0] for c in Player.Position.choices}
    for p in squad:
        player_id = p.get("id")
        if not player_id:
            continue

        raw_pos = p.get("position") or ""
        position = raw_pos if raw_pos in valid_positions else ""

        Player.objects.update_or_create(
            id=player_id,
            defaults={
                "team": team,
                "name": p.get("name", ""),
                "nationality": p.get("nationality") or "",
                "position": position,
                "shirt_number": p.get("shirtNumber"),
                "date_of_birth": _parse_date(p.get("dateOfBirth")),
            },
        )
        incoming_ids.add(player_id)

    # Remove players no longer in this team's squad
    removed = Player.objects.filter(team=team).exclude(id__in=incoming_ids).delete()
    if removed[0]:
        logger.info(f"    Removed {removed[0]} stale player(s) from {team.name}")


def sync_standings(
    client: FootballDataClient,
    competition: Competition,
) -> None:
    """
    Fetch /competitions/{code}/standings and upsert Standing + TableEntry rows.

    The API returns up to three table types (TOTAL, HOME, AWAY). For each:
      - update_or_create the Standing row (unique on competition+type+stage)
      - delete stale TableEntry rows (team left/relegated), then upsert current rows
    Season dates come from the response's 'season' object.
    """
    data = client.get(f"/competitions/{competition.code}/standings")

    season = data.get("season") or {}
    season_start = _parse_date(season.get("startDate"))
    season_end = _parse_date(season.get("endDate"))

    valid_types = {c[0] for c in Standing.TableType.choices}
    for table_data in data.get("standings", []):
        table_type = table_data.get("type", "TOTAL").upper()
        stage = table_data.get("stage") or ""

        if table_type not in valid_types:
            logger.warning(f"  Unknown standings type '{table_type}', skipping")
            continue

        standing, created = Standing.objects.update_or_create(
            competition=competition,
            type=table_type,
            stage=stage,
            defaults={
                "season_start_date": season_start,
                "season_end_date": season_end,
            },
        )
        action = "Created" if created else "Updated"
        logger.info(f"  {action} standing: {standing}")

        rows = table_data.get("table", [])
        incoming_team_ids = set()

        # Bulk-fetch all teams referenced in this table to avoid N+1 queries.
        row_team_ids = {
            row["team"]["id"]
            for row in rows
            if row.get("team", {}).get("id")
        }
        teams_map = {t.id: t for t in Team.objects.filter(id__in=row_team_ids)}

        with transaction.atomic():
            for row in rows:
                team_data = row.get("team", {})
                team_id = team_data.get("id")
                if not team_id:
                    continue

                team = teams_map.get(team_id)
                if team is None:
                    logger.warning(
                        f"    Team id={team_id} not in DB; run teams sync first. Skipping."
                    )
                    continue

                TableEntry.objects.update_or_create(
                    standing=standing,
                    team=team,
                    defaults={
                        "position": row.get("position", 0),
                        "played_games": row.get("playedGames", 0),
                        "won": row.get("won", 0),
                        "draw": row.get("draw", 0),
                        "lost": row.get("lost", 0),
                        "points": row.get("points", 0),
                        "goals_for": row.get("goalsFor", 0),
                        "goals_against": row.get("goalsAgainst", 0),
                        "goal_difference": row.get("goalDifference", 0),
                    },
                )
                incoming_team_ids.add(team_id)

            # Remove teams no longer in the table (e.g., format change)
            removed = (
                TableEntry.objects
                .filter(standing=standing)
                .exclude(team_id__in=incoming_team_ids)
                .delete()
            )
            if removed[0]:
                logger.info(f"    Removed {removed[0]} stale table entry/entries")

        logger.info(f"    {len(incoming_team_ids)} table entries synced")


def sync_matches(
    client: FootballDataClient,
    competition: Competition,
    matchday: Optional[int] = None,
) -> int:
    """
    Fetch /competitions/{code}/matches and upsert Match rows.

    - No filter  → API default (returns today's window; typically last+next week)
    - matchday=N → only that matchday

    Returns count of upserted matches.
    """
    params: dict[str, Any] = {}
    if matchday is not None:
        params["matchday"] = matchday
        logger.info(f"  Fetching matches for matchday {matchday}…")
    else:
        logger.info("  Fetching default window matches…")

    data = client.get(f"/competitions/{competition.code}/matches", params=params or None)
    raw_matches = data.get("matches", [])

    # Bulk-fetch all teams referenced in these matches to avoid N+1 queries.
    team_ids = {
        tid
        for m in raw_matches
        for tid in (m.get("homeTeam", {}).get("id"), m.get("awayTeam", {}).get("id"))
        if tid
    }
    teams_map = {t.id: t for t in Team.objects.filter(id__in=team_ids)}

    valid_statuses = {s[0] for s in Match.Status.choices}
    upserted = 0

    for m in raw_matches:
        home_id = m.get("homeTeam", {}).get("id")
        away_id = m.get("awayTeam", {}).get("id")

        home_team = teams_map.get(home_id) if home_id else None
        away_team = teams_map.get(away_id) if away_id else None

        score = m.get("score", {})
        ft = score.get("fullTime", {}) or {}
        ht = score.get("halfTime", {}) or {}

        raw_status = m.get("status", "")
        status = raw_status if raw_status in valid_statuses else "SCHEDULED"

        utc_date = _parse_dt(m.get("utcDate"))
        if utc_date is None:
            logger.warning(f"  Match id={m.get('id')} has no utcDate, skipping")
            continue

        Match.objects.update_or_create(
            id=m["id"],
            defaults={
                "competition": competition,
                "utc_date": utc_date,
                "status": status,
                "matchday": m.get("matchday"),
                "stage": m.get("stage") or "",
                "home_team": home_team,
                "away_team": away_team,
                "score_home_ft": ft.get("home"),
                "score_away_ft": ft.get("away"),
                "score_home_ht": ht.get("home"),
                "score_away_ht": ht.get("away"),
            },
        )
        upserted += 1

    return upserted


# ─── Command ──────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = (
        "Sync Football-Data.org data into the Django DB. "
        "Always syncs competition, teams, standings. "
        "Use --matchday or --full to control which matches are fetched."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--competition",
            type=str,
            required=True,
            metavar="CODE",
            help="Competition code, e.g. PL, BL1, SA, PD, FL1",
        )
        parser.add_argument(
            "--matchday",
            type=int,
            default=None,
            metavar="N",
            help="Sync only this matchday's matches (1-38 for PL)",
        )
        parser.add_argument(
            "--full",
            action="store_true",
            default=False,
            help="Sync the full season: all matches + player squad data.",
        )

    def handle(self, *args, **options) -> None:
        code = options["competition"].upper()
        matchday: Optional[int] = options["matchday"]
        full: bool = options["full"]

        api_key = settings.FOOTBALL_DATA_API_KEY
        base_url = settings.FOOTBALL_DATA_BASE_URL
        client = FootballDataClient(api_key=api_key, base_url=base_url)

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\n⚽  FootyLens sync — competition={code}"
            + (f"  matchday={matchday}" if matchday else "")
            + ("  [+squad]" if full else "")
        ))

        # ── 1. Competition ───────────────────────────────────────────────────
        self.stdout.write("\n[1/4] Syncing competition…")
        competition = sync_competition(client, code)
        self.stdout.write(self.style.SUCCESS(f"  ✓ {competition}"))
        time.sleep(CALL_SLEEP)

        # ── 2. Teams (+ players if --full) ───────────────────────────────────
        self.stdout.write(
            f"\n[2/4] Syncing teams"
            + (" + squad" if full else " (basic info only)")
            + "…"
        )
        teams = sync_teams(client, competition, sync_players=full)
        self.stdout.write(self.style.SUCCESS(f"  ✓ {len(teams)} teams synced"))
        time.sleep(CALL_SLEEP)

        # ── 3. Standings ─────────────────────────────────────────────────────
        self.stdout.write("\n[3/4] Syncing standings…")
        sync_standings(client, competition)
        self.stdout.write(self.style.SUCCESS("  ✓ standings synced"))
        time.sleep(CALL_SLEEP)

        # ── 4. Matches ───────────────────────────────────────────────────────
        self.stdout.write("\n[4/4] Syncing matches…")
        count = sync_matches(
            client,
            competition,
            matchday=matchday,
        )
        self.stdout.write(self.style.SUCCESS(f"  ✓ {count} matches synced"))

        self.stdout.write(self.style.SUCCESS("\n✅  Sync complete.\n"))
