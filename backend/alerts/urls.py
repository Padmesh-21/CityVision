from rest_framework.routers import DefaultRouter

from .views import AlertViewSet, BlacklistViewSet

router = DefaultRouter()
router.register("blacklist", BlacklistViewSet, basename="blacklist")
router.register("alerts", AlertViewSet, basename="alert")

urlpatterns = router.urls
