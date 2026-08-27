from django.contrib.auth import get_user_model
from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated

from .permissions import IsAdminRole
from .serializers import UserCreateSerializer, UserSerializer

User = get_user_model()


class MeView(generics.RetrieveAPIView):
    """Returns the currently authenticated dashboard user."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self) -> User:
        return self.request.user


class UserViewSet(viewsets.ModelViewSet):
    """ADMIN-only management of dashboard user accounts."""

    queryset = User.objects.all().order_by("username")
    permission_classes = [IsAdminRole]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer
