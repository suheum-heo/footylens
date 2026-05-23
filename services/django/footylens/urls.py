"""
Root URL configuration for FootyLens Django app.

/admin/              — Django admin
/api/competitions/   — Competition list/detail (matches app)
/api/matches/        — Match list/detail (matches app)
/api/teams/          — Team list/detail (teams app)
/api/standings/      — Standing list/detail (standings app)
/api/auth/token/          — Obtain JWT pair
/api/auth/token/refresh/  — Refresh access token
"""

from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    # DRF browsable API auth
    path("api-auth/", include("rest_framework.urls")),
    # App API routes
    path("api/", include("matches.urls")),
    path("api/", include("teams.urls")),
    path("api/", include("standings.urls")),
    # JWT auth
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
