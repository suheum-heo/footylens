"""
Match-related models.

Competition and Match are owned by this app.
Match references teams.Team via FK (cross-app FK — Django resolves these cleanly).
"""

from django.db import models


class Competition(models.Model):
    """
    A football competition/league (e.g., Premier League, Bundesliga).
    id is sourced from Football-Data.org — we keep their IDs to simplify sync.
    """

    id = models.IntegerField(primary_key=True)  # Football-Data.org competition id
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True, db_index=True)
    area_name = models.CharField(max_length=100, blank=True)
    area_code = models.CharField(max_length=5, blank=True)
    emblem_url = models.URLField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Competition"
        verbose_name_plural = "Competitions"

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class Match(models.Model):
    """
    A single football match.
    Scores are stored as nullable ints — null means the match hasn't been played yet.
    """

    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        TIMED = "TIMED", "Timed"
        IN_PLAY = "IN_PLAY", "In Play"
        PAUSED = "PAUSED", "Paused"
        FINISHED = "FINISHED", "Finished"
        SUSPENDED = "SUSPENDED", "Suspended"
        POSTPONED = "POSTPONED", "Postponed"
        CANCELLED = "CANCELLED", "Cancelled"
        AWARDED = "AWARDED", "Awarded"

    id = models.IntegerField(primary_key=True)  # Football-Data.org match id
    competition = models.ForeignKey(
        Competition, on_delete=models.CASCADE, related_name="matches"
    )
    utc_date = models.DateTimeField(db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, db_index=True)
    matchday = models.PositiveSmallIntegerField(null=True, blank=True, db_index=True)
    stage = models.CharField(max_length=50, blank=True)

    # Teams — cross-app FK resolved at runtime by Django
    home_team = models.ForeignKey(
        "teams.Team", on_delete=models.SET_NULL, null=True, related_name="home_matches"
    )
    away_team = models.ForeignKey(
        "teams.Team", on_delete=models.SET_NULL, null=True, related_name="away_matches"
    )

    # Full-time score
    score_home_ft = models.SmallIntegerField(null=True, blank=True)
    score_away_ft = models.SmallIntegerField(null=True, blank=True)
    # Half-time score
    score_home_ht = models.SmallIntegerField(null=True, blank=True)
    score_away_ht = models.SmallIntegerField(null=True, blank=True)

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-utc_date"]
        verbose_name = "Match"
        verbose_name_plural = "Matches"
        indexes = [
            models.Index(fields=["competition", "matchday"]),
            models.Index(fields=["competition", "status"]),
        ]

    def __str__(self) -> str:
        home = self.home_team.name if self.home_team else "TBD"
        away = self.away_team.name if self.away_team else "TBD"
        return f"{home} vs {away} ({self.utc_date:%Y-%m-%d})"

    @property
    def score_display(self) -> str:
        if self.score_home_ft is None or self.score_away_ft is None:
            return "-"
        return f"{self.score_home_ft}–{self.score_away_ft}"
