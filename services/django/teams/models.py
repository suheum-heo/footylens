"""
Team and Player models.
"""

from django.db import models


class Team(models.Model):
    """
    A football club.
    id is sourced from Football-Data.org — kept as-is to simplify sync.
    """

    id = models.IntegerField(primary_key=True)  # Football-Data.org team id
    name = models.CharField(max_length=100, db_index=True)
    short_name = models.CharField(max_length=50, blank=True)
    tla = models.CharField(max_length=5, blank=True)  # Three-letter abbreviation
    founded = models.PositiveSmallIntegerField(null=True, blank=True)
    crest_url = models.URLField(blank=True)
    venue = models.CharField(max_length=200, blank=True)
    area_name = models.CharField(max_length=100, blank=True)
    area_code = models.CharField(max_length=5, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Team"
        verbose_name_plural = "Teams"

    def __str__(self) -> str:
        return self.name


class Player(models.Model):
    """
    A player currently or previously registered to a team.
    Populated from the Football-Data.org /teams/{id} endpoint.
    """

    class Position(models.TextChoices):
        GOALKEEPER = "Goalkeeper", "Goalkeeper"
        DEFENCE = "Defence", "Defence"
        MIDFIELD = "Midfield", "Midfield"
        OFFENCE = "Offence", "Offence"

    id = models.IntegerField(primary_key=True)  # Football-Data.org person id
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="players")
    name = models.CharField(max_length=100, db_index=True)
    nationality = models.CharField(max_length=100, blank=True)
    position = models.CharField(
        max_length=20, choices=Position.choices, blank=True
    )
    shirt_number = models.PositiveSmallIntegerField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["team", "shirt_number", "name"]
        verbose_name = "Player"
        verbose_name_plural = "Players"

    def __str__(self) -> str:
        return f"{self.name} ({self.team.tla or self.team.name})"
