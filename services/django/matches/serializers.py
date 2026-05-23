from rest_framework import serializers
from .models import Competition, Match


class CompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition
        fields = ["id", "name", "code", "area_name", "area_code", "emblem_url"]


class MatchSerializer(serializers.ModelSerializer):
    """
    List serializer: includes nested team names for direct consumption.
    Avoids N+1 via select_related in the viewset queryset.
    """

    competition_name = serializers.CharField(source="competition.name", read_only=True)
    competition_code = serializers.CharField(source="competition.code", read_only=True)
    home_team_name = serializers.CharField(source="home_team.name", read_only=True)
    away_team_name = serializers.CharField(source="away_team.name", read_only=True)
    home_team_tla = serializers.CharField(source="home_team.tla", read_only=True)
    away_team_tla = serializers.CharField(source="away_team.tla", read_only=True)
    score = serializers.SerializerMethodField()

    class Meta:
        model = Match
        fields = [
            "id",
            "competition",
            "competition_name",
            "competition_code",
            "utc_date",
            "status",
            "matchday",
            "stage",
            "home_team",
            "home_team_name",
            "home_team_tla",
            "away_team",
            "away_team_name",
            "away_team_tla",
            "score",
            "last_updated",
        ]

    def get_score(self, obj: Match) -> dict:
        return {
            "fullTime": {
                "home": obj.score_home_ft,
                "away": obj.score_away_ft,
            },
            "halfTime": {
                "home": obj.score_home_ht,
                "away": obj.score_away_ht,
            },
        }
