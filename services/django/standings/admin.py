from django.contrib import admin
from .models import Standing, TableEntry


class TableEntryInline(admin.TabularInline):
    model = TableEntry
    extra = 0
    fields = (
        "position", "team", "played_games",
        "won", "draw", "lost", "points",
        "goals_for", "goals_against", "goal_difference",
    )
    raw_id_fields = ("team",)
    ordering = ("position",)


@admin.register(Standing)
class StandingAdmin(admin.ModelAdmin):
    list_display = ("id", "competition", "type", "stage", "last_updated")
    list_filter = ("competition", "type")
    ordering = ("competition", "type")
    readonly_fields = ("last_updated",)
    inlines = [TableEntryInline]


@admin.register(TableEntry)
class TableEntryAdmin(admin.ModelAdmin):
    list_display = (
        "position", "team", "standing",
        "played_games", "won", "draw", "lost",
        "points", "goal_difference",
    )
    list_filter = ("standing__competition", "standing__type")
    search_fields = ("team__name",)
    raw_id_fields = ("standing", "team")
    ordering = ("standing", "position")
