from rest_framework.routers import DefaultRouter

from .views import CameraViewSet

router = DefaultRouter()
router.register("", CameraViewSet, basename="camera")

urlpatterns = router.urls
