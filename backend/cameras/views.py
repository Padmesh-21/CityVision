from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.permissions import IsAdminOrOperatorOrReadOnly

from .models import Camera, generate_api_key
from .serializers import CameraAPIKeySerializer, CameraSerializer


class CameraViewSet(viewsets.ModelViewSet):
    queryset = Camera.objects.all()
    serializer_class = CameraSerializer
    permission_classes = [IsAdminOrOperatorOrReadOnly]

    def create(self, request, *args, **kwargs):
        """On creation only, include the freshly generated api_key so the
        operator can configure the new edge camera node. It is never
        exposed again through list/retrieve."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        camera = serializer.save()
        data = {**serializer.data, "api_key": camera.api_key}
        headers = self.get_success_headers(serializer.data)
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def regenerate_api_key(self, request, pk=None):
        """ADMIN-only: rotate a camera's API key, e.g. after a suspected leak."""
        if request.user.role != "ADMIN":
            return Response(
                {"detail": "Only ADMIN can regenerate API keys."},
                status=status.HTTP_403_FORBIDDEN,
            )
        camera = self.get_object()
        camera.api_key = generate_api_key()
        camera.save(update_fields=["api_key"])
        return Response(CameraAPIKeySerializer(camera).data)
