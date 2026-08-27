"""Shared query-param filtering for the analytics endpoints (date range,
camera, vehicle -- per the dashboard's filter requirements).

`include_camera` exists because route-density/average-speed are about
movement *between* cameras: filtering their base queryset down to a
single camera first would remove one side of every consecutive-detection
pair, leaving no routes at all. Those two views pass include_camera=False.
"""

from django.db.models import QuerySet
from django.utils.dateparse import parse_date
from rest_framework.request import Request

from vehicles.models import normalize_plate


def apply_common_filters(
    queryset: QuerySet, request: Request, *, include_camera: bool = True
) -> QuerySet:
    if include_camera:
        camera_code = request.query_params.get("camera")
        if camera_code:
            queryset = queryset.filter(camera__camera_code=camera_code)

    start_date = request.query_params.get("start_date")
    if start_date and (parsed := parse_date(start_date)):
        queryset = queryset.filter(timestamp__date__gte=parsed)

    end_date = request.query_params.get("end_date")
    if end_date and (parsed := parse_date(end_date)):
        queryset = queryset.filter(timestamp__date__lte=parsed)

    plate_number = request.query_params.get("vehicle")
    if plate_number:
        queryset = queryset.filter(vehicle__plate_number=normalize_plate(plate_number))

    return queryset
