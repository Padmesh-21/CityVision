"""Trajectory reconstruction.

A vehicle's trajectory is never stored -- it's derived by ordering its
Detection rows chronologically (see Step 1 / docs/database.md: no
separate trajectory table). This is the one place that query lives, so
analytics (route density, average speed) can reuse the same building
block instead of re-deriving it.
"""

from django.db.models import QuerySet

from detections.models import Detection
from vehicles.models import Vehicle


def get_vehicle_trajectory(vehicle: Vehicle) -> QuerySet[Detection]:
    return (
        Detection.objects.filter(vehicle=vehicle)
        .select_related("camera")
        .order_by("timestamp")
    )
