from rest_framework import serializers
from .models import Standing, TableEntry


class TableEntrySerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source="team.name", read_only=True)
    team_tla = serializers.CharField(source="team.tla", read_only=True)
    team_crest = serializers.URLField(source="team.crest_url", read_only=True)

    class Meta:
        model = TableEntry
        fields = [
            "position", "team", "team_name", "team_tla", "team_crest",
            "played_games", "won", "draw", "lost",
            "points", "goals_for", "goals_against", "goal_difference",
        ]


class StandingSerializer(serializers.ModelSerializer):
    """List view — no nested table to avoid heavy payloads on list endpoints."""

    competition_name = serializers.CharField(source="competition.name", read_only=True)
    competition_code = serializers.CharField(source="competition.code", read_only=True)

    class Meta:
        model = Standing
        fields = [
            "id", "competition", "competition_name", "competition_code",
            "type", "stage", "season_start_date", "season_end_date",
            "last_updated",
        ]


class StandingDetailSerializer(StandingSerializer):
    """Detail view — includes full table, ordered by position."""

    table = TableEntrySerializer(many=True, read_only=True)

    class Meta(StandingSerializer.Meta):
        fields = StandingSerializer.Meta.fields + ["table"]
