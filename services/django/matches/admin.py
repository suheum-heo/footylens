from django.contrib import admin
from .models import Competition, Match


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "code", "area_name")
    search_fields = ("name", "code")
    ordering = ("name",)


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "competition",
        "utc_date",
        "home_team",
        "score_display",
        "away_team",
        "status",
        "matchday",
    )
    list_filter = ("competition", "status", "matchday", "stage")
    search_fields = ("home_team__name", "away_team__name")
    raw_id_fields = ("home_team", "away_team")
    ordering = ("-utc_date",)
    readonly_fields = ("last_updated",)

    @admin.display(description="Score")
    def score_display(self, obj: Match) -> str:
        return obj.score_display
