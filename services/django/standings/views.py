from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Standing
from .serializers import StandingSerializer, StandingDetailSerializer


class StandingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list:   GET /api/standings/       ?competition=PL&type=TOTAL
    detail: GET /api/standings/{id}/   — includes full table
    """

    permission_classes = [IsAuthenticatedOrReadOnly]
    ordering_fields = ["competition__code", "type"]
    ordering = ["competition", "type"]

    def get_queryset(self):
        qs = Standing.objects.select_related("competition").prefetch_related(
            "table__team"
        )
        params = self.request.query_params

        competition = params.get("competition")
        if competition:
            qs = qs.filter(competition__code__iexact=competition)

        table_type = params.get("type")
        if table_type:
            qs = qs.filter(type__iexact=table_type)

        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return StandingDetailSerializer
        return StandingSerializer
