"""Traffic analytics -- same principle as trajectory reconstruction:
nothing here is precomputed or stored, it's all queried live from
Detection rows. At prototype scale this is simple and correct; if the
Detection table grows large enough that the Python-side grouping in
`_consecutive_camera_pairs` becomes a bottleneck, that's a Step 9
(optimization) concern, not a Step 5 one.
"""

from collections import defaultdict
from itertools import pairwise

from django.db.models import Count, QuerySet
from django.utils import timezone

from detections.models import Detection

from .geo import haversine_km


def vehicle_and_detection_counts(queryset: QuerySet[Detection]) -> dict:
    return {
        "total_detections": queryset.count(),
        "unique_vehicles": queryset.values("vehicle_id").distinct().count(),
    }


def detections_per_camera(queryset: QuerySet[Detection]) -> list[dict]:
    rows = (
        queryset.values("camera__camera_code", "camera__location_name")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    return [
        {
            "camera": row["camera__camera_code"],
            "location": row["camera__location_name"],
            "count": row["count"],
        }
        for row in rows
    ]


def hourly_traffic(queryset: QuerySet[Detection]) -> list[dict]:
    """Traffic by hour of day, in the project's local time zone
    (Asia/Kolkata) rather than the UTC the timestamps are stored in --
    an hourly pattern is only meaningful against local wall-clock time.

    Bucketed in Python rather than via MySQL's EXTRACT(... CONVERT_TZ
    ...), which requires the named-timezone tables to be loaded
    (`mysql_tzinfo_to_sql`) -- not set up by default on a typical
    Windows MySQL install, and it fails *silently* (every row's hour
    comes back NULL) rather than raising an error, which is exactly the
    "don't claim a number you haven't verified" trap this project is
    trying to avoid elsewhere (see camera_node/evaluate.py).
    """
    counts = [0] * 24
    for ts in queryset.values_list("timestamp", flat=True):
        counts[timezone.localtime(ts).hour] += 1
    return [{"hour": hour, "count": count} for hour, count in enumerate(counts)]


def _consecutive_camera_pairs(queryset: QuerySet[Detection]):
    """For each vehicle, walk its detections in chronological order and
    yield (earlier, later) for each consecutive pair at DIFFERENT
    cameras -- the shared basis for both route density and average
    speed, since both describe movement between cameras."""
    by_vehicle = defaultdict(list)
    for detection in queryset.select_related("camera").order_by("vehicle_id", "timestamp"):
        by_vehicle[detection.vehicle_id].append(detection)

    for detections in by_vehicle.values():
        for earlier, later in pairwise(detections):
            if earlier.camera_id != later.camera_id:
                yield earlier, later


def route_density(queryset: QuerySet[Detection]) -> list[dict]:
    counts: dict[tuple[str, str], int] = defaultdict(int)
    labels: dict[tuple[str, str], tuple[str, str]] = {}

    for earlier, later in _consecutive_camera_pairs(queryset):
        key = (earlier.camera.camera_code, later.camera.camera_code)
        counts[key] += 1
        labels[key] = (earlier.camera.location_name, later.camera.location_name)

    return [
        {
            "from_camera": from_code,
            "from_location": labels[(from_code, to_code)][0],
            "to_camera": to_code,
            "to_location": labels[(from_code, to_code)][1],
            "count": count,
        }
        for (from_code, to_code), count in sorted(counts.items(), key=lambda kv: -kv[1])
    ]


def estimated_average_speed(queryset: QuerySet[Detection]) -> list[dict]:
    """Estimated average speed between camera locations, derived from
    (distance between camera coordinates) / (time between consecutive
    detections of the same vehicle). This is NOT an instantaneous
    vehicle speed measurement -- see the `note` returned alongside this
    in the API response."""
    samples: dict[tuple[str, str], list[tuple[float, float]]] = defaultdict(list)
    labels: dict[tuple[str, str], tuple[str, str, float]] = {}

    for earlier, later in _consecutive_camera_pairs(queryset):
        seconds = (later.timestamp - earlier.timestamp).total_seconds()
        if seconds <= 0:
            continue

        distance_km = haversine_km(
            float(earlier.latitude),
            float(earlier.longitude),
            float(later.latitude),
            float(later.longitude),
        )
        speed_kmh = distance_km / (seconds / 3600)

        key = (earlier.camera.camera_code, later.camera.camera_code)
        samples[key].append((seconds, speed_kmh))
        labels[key] = (earlier.camera.location_name, later.camera.location_name, distance_km)

    results = []
    for (from_code, to_code), values in samples.items():
        from_location, to_location, distance_km = labels[(from_code, to_code)]
        seconds_list = [v[0] for v in values]
        speeds = [v[1] for v in values]
        results.append(
            {
                "from_camera": from_code,
                "from_location": from_location,
                "to_camera": to_code,
                "to_location": to_location,
                "distance_km": round(distance_km, 3),
                "sample_count": len(values),
                "avg_time_seconds": round(sum(seconds_list) / len(seconds_list), 1),
                "estimated_avg_speed_kmh": round(sum(speeds) / len(speeds), 1),
            }
        )
    return sorted(results, key=lambda r: -r["sample_count"])


def heatmap_points(queryset: QuerySet[Detection]) -> list[dict]:
    rows = queryset.values(
        "camera__camera_code", "camera__location_name", "camera__latitude", "camera__longitude"
    ).annotate(weight=Count("id"))

    return [
        {
            "camera": row["camera__camera_code"],
            "location": row["camera__location_name"],
            "latitude": row["camera__latitude"],
            "longitude": row["camera__longitude"],
            "weight": row["weight"],
        }
        for row in rows
    ]
