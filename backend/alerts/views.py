from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsAdminOrOperatorOrReadOnly

from .models import Alert, Blacklist
from .serializers import AlertSerializer, BlacklistSerializer


class BlacklistViewSet(viewsets.ModelViewSet):
    queryset = Blacklist.objects.all()
    serializer_class = BlacklistSerializer
    permission_classes = [IsAdminOrOperatorOrReadOnly]


class AlertViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Read-only for now. Step 8 adds acknowledge/resolve actions and the
    WebSocket broadcast when a new alert is created."""

    queryset = Alert.objects.select_related("vehicle", "detection__camera").all()
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]
