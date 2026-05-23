from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Competition, Match
from .serializers import CompetitionSerializer, MatchSerializer


class CompetitionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list:   GET /api/competitions/
    detail: GET /api/competitions/{id}/
    """

    queryset = Competition.objects.all()
    serializer_class = CompetitionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "code"]


class MatchViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list:   GET /api/matches/          ?competition=PL&status=FINISHED&matchday=38
    detail: GET /api/matches/{id}/
    """

    serializer_class = MatchSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    search_fields = ["home_team__name", "away_team__name"]
    ordering_fields = ["utc_date", "matchday"]
    ordering = ["-utc_date"]

    def get_queryset(self):
        qs = Match.objects.select_related(
            "competition", "home_team", "away_team"
        )
        params = self.request.query_params

        competition = params.get("competition")
        if competition:
            qs = qs.filter(competition__code__iexact=competition)

        status = params.get("status")
        if status:
            qs = qs.filter(status__iexact=status)

        matchday = params.get("matchday")
        if matchday and matchday.isdigit():
            qs = qs.filter(matchday=int(matchday))

        return qs
