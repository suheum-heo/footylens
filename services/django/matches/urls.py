from rest_framework.routers import DefaultRouter
from .views import CompetitionViewSet, MatchViewSet

router = DefaultRouter()
router.register("competitions", CompetitionViewSet, basename="competition")
router.register("matches", MatchViewSet, basename="match")

urlpatterns = router.urls
