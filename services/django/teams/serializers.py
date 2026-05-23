from rest_framework import serializers
from .models import Team, Player


class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = [
            "id", "name", "nationality", "position",
            "shirt_number", "date_of_birth",
        ]


class TeamSerializer(serializers.ModelSerializer):
    """List view — no nested players to keep payload small."""

    class Meta:
        model = Team
        fields = [
            "id", "name", "short_name", "tla",
            "founded", "crest_url", "venue",
            "area_name", "area_code",
        ]


class TeamDetailSerializer(TeamSerializer):
    """Detail view — includes squad."""

    players = PlayerSerializer(many=True, read_only=True)

    class Meta(TeamSerializer.Meta):
        fields = TeamSerializer.Meta.fields + ["players"]
