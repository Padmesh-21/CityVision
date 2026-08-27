from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from detections.models import Detection

from .filters import apply_common_filters
from .services import (
    detections_per_camera,
    estimated_average_speed,
    heatmap_points,
    hourly_traffic,
    route_density,
    vehicle_and_detection_counts,
)


class AnalyticsSummaryView(APIView):
    """GET /api/analytics/summary/?camera=&start_date=&end_date=&vehicle=

    Combined dashboard widget data: totals, per-camera counts, hourly
    traffic pattern.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = apply_common_filters(Detection.objects.all(), request)
        data = vehicle_and_detection_counts(queryset)
        data["detections_per_camera"] = detections_per_camera(queryset)
        data["hourly_traffic"] = hourly_traffic(queryset)
        return Response(data)


class RouteDensityView(APIView):
    """GET /api/analytics/route-density/?start_date=&end_date=&vehicle=

    Vehicle counts for each camera-to-camera route, derived from
    consecutive detections of the same vehicle. `camera` filtering isn't
    offered here -- it would remove one side of every route.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = apply_common_filters(Detection.objects.all(), request, include_camera=False)
        return Response({"routes": route_density(queryset)})


class AverageSpeedView(APIView):
    """GET /api/analytics/average-speed/?start_date=&end_date=&vehicle=

    Estimated average speed between camera locations -- see the `note`
    in the response. Not an instantaneous vehicle speed measurement.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = apply_common_filters(Detection.objects.all(), request, include_camera=False)
        return Response(
            {
                "note": (
                    "Estimated average speed between camera locations, derived from "
                    "distance-between-cameras / time-between-consecutive-detections "
                    "of the same vehicle. Not an instantaneous vehicle speed measurement."
                ),
                "routes": estimated_average_speed(queryset),
            }
        )


class HeatmapView(APIView):
    """GET /api/analytics/heatmap/?camera=&start_date=&end_date=&vehicle=

    Per-camera detection density, for a Leaflet heatmap layer.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = apply_common_filters(Detection.objects.all(), request)
        return Response({"points": heatmap_points(queryset)})
