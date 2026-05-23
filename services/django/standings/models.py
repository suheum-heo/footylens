"""
Standings models.

Standing = one snapshot of a table (e.g., PL overall, MD 38).
TableEntry = one row in that table.
"""

from django.db import models


class Standing(models.Model):
    """
    A league standings snapshot for a competition.
    type distinguishes TOTAL / HOME / AWAY tables.
    unique_together prevents duplicate snapshots for the same competition+type+stage.
    """

    class TableType(models.TextChoices):
        TOTAL = "TOTAL", "Total"
        HOME = "HOME", "Home"
        AWAY = "AWAY", "Away"

    competition = models.ForeignKey(
        "matches.Competition", on_delete=models.CASCADE, related_name="standings"
    )
    season_start_date = models.DateField(null=True, blank=True)
    season_end_date = models.DateField(null=True, blank=True)
    type = models.CharField(max_length=10, choices=TableType.choices, default=TableType.TOTAL)
    stage = models.CharField(max_length=50, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["competition", "type"]
        verbose_name = "Standing"
        verbose_name_plural = "Standings"
        unique_together = [("competition", "type", "stage")]

    def __str__(self) -> str:
        return f"{self.competition.code} — {self.type}"


class TableEntry(models.Model):
    """
    One row in a standings table: team position, record, and points.
    """

    standing = models.ForeignKey(Standing, on_delete=models.CASCADE, related_name="table")
    team = models.ForeignKey("teams.Team", on_delete=models.CASCADE, related_name="table_entries")
    position = models.PositiveSmallIntegerField()
    played_games = models.PositiveSmallIntegerField(default=0)
    won = models.PositiveSmallIntegerField(default=0)
    draw = models.PositiveSmallIntegerField(default=0)
    lost = models.PositiveSmallIntegerField(default=0)
    points = models.PositiveSmallIntegerField(default=0)
    goals_for = models.PositiveSmallIntegerField(default=0)
    goals_against = models.PositiveSmallIntegerField(default=0)
    goal_difference = models.SmallIntegerField(default=0)

    class Meta:
        ordering = ["standing", "position"]
        verbose_name = "Table Entry"
        verbose_name_plural = "Table Entries"
        unique_together = [("standing", "team")]

    def __str__(self) -> str:
        return f"{self.position}. {self.team.name} — {self.points}pts"
