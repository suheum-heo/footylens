from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Team
from .serializers import TeamSerializer, TeamDetailSerializer


class TeamViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list:   GET /api/teams/       ?competition=PL
    detail: GET /api/teams/{id}/   — includes squad
    """

    permission_classes = [IsAuthenticatedOrReadOnly]
    search_fields = ["name", "tla", "short_name"]
    ordering_fields = ["name", "founded"]
    ordering = ["name"]

    def get_queryset(self):
        qs = Team.objects.prefetch_related("players")
        competition = self.request.query_params.get("competition")
        if competition:
            # Filter teams that played in at least one match in this competition
            qs = qs.filter(
                home_matches__competition__code__iexact=competition
            ).distinct()
        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return TeamDetailSerializer
        return TeamSerializer
