from rest_framework.routers import DefaultRouter
from .views import StandingViewSet

router = DefaultRouter()
router.register("standings", StandingViewSet, basename="standing")

urlpatterns = router.urls
