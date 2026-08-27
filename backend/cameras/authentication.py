from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import Camera


class CameraAPIKeyAuthentication(BaseAuthentication):
    """Authenticates an edge camera node via the `X-API-Key` header.

    Camera nodes are not Django Users, so on success this sets
    request.user to AnonymousUser and request.auth to the Camera instance
    -- views that accept camera traffic (e.g. detection creation) read
    `request.auth` to know which camera is posting.
    """

    def authenticate(self, request):
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return None
        try:
            camera = Camera.objects.get(api_key=api_key)
        except Camera.DoesNotExist as exc:
            raise AuthenticationFailed("Invalid camera API key.") from exc
        return (AnonymousUser(), camera)
