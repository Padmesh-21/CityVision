from rest_framework.permissions import BasePermission

from .models import Camera


class IsAuthenticatedCamera(BasePermission):
    """Grants access only when the request was authenticated as a Camera
    via CameraAPIKeyAuthentication (request.auth is a Camera instance)."""

    def has_permission(self, request, view) -> bool:
        return isinstance(request.auth, Camera)
