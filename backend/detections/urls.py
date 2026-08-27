from rest_framework.routers import DefaultRouter

from .views import DetectionViewSet

router = DefaultRouter()
router.register("", DetectionViewSet, basename="detection")

urlpatterns = router.urls
