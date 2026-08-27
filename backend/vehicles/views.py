from django.shortcuts import get_object_or_404
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Vehicle, normalize_plate
from .serializers import VehicleSerializer


class VehicleViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Read-only: vehicles are created implicitly from detections, not via
    this API (see detections.services.process_detection)."""

    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "plate_number"
    lookup_value_regex = "[^/]+"

    def get_object(self):
        normalized = normalize_plate(self.kwargs[self.lookup_url_kwarg or self.lookup_field])
        obj = get_object_or_404(self.get_queryset(), plate_number=normalized)
        self.check_object_permissions(self.request, obj)
        return obj
