from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from cameras.authentication import CameraAPIKeyAuthentication
from cameras.permissions import IsAuthenticatedCamera

from .models import Detection
from .serializers import DetectionCreateSerializer, DetectionSerializer
from .services import process_detection


class DetectionViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    - POST (create): edge camera nodes only, authenticated via X-API-Key.
    - GET (list/retrieve): dashboard users only, authenticated via JWT.
    """

    queryset = Detection.objects.select_related("camera", "vehicle").all()
    authentication_classes = [CameraAPIKeyAuthentication, JWTAuthentication]

    def get_serializer_class(self):
        if self.action == "create":
            return DetectionCreateSerializer
        return DetectionSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticatedCamera()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        camera = request.auth  # set by CameraAPIKeyAuthentication

        body_camera_id = request.data.get("camera_id")
        if not body_camera_id:
            return Response(
                {"success": False, "error": "camera_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if body_camera_id != camera.camera_code:
            return Response(
                {"success": False, "error": "camera_id does not match the authenticated camera."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        detection, alert_generated = process_detection(camera, serializer.validated_data)

        return Response(
            {
                "success": True,
                "detection_id": detection.id,
                "vehicle_id": detection.vehicle_id,
                "alert_generated": alert_generated,
            },
            status=status.HTTP_201_CREATED,
        )
