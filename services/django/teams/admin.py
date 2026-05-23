from django.contrib import admin
from .models import Team, Player


class PlayerInline(admin.TabularInline):
    model = Player
    extra = 0
    fields = ("id", "name", "position", "shirt_number", "nationality", "date_of_birth")
    readonly_fields = ("id",)
    ordering = ("shirt_number", "name")


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "tla", "short_name", "area_name", "founded")
    search_fields = ("name", "tla", "short_name")
    list_filter = ("area_name",)
    ordering = ("name",)
    inlines = [PlayerInline]


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "team", "position", "shirt_number", "nationality")
    list_filter = ("position", "nationality")
    search_fields = ("name", "team__name")
    raw_id_fields = ("team",)
    ordering = ("team", "shirt_number")
