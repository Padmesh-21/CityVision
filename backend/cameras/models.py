import secrets

from django.db import models


def generate_api_key() -> str:
    return secrets.token_hex(32)


class Camera(models.Model):
    """A single edge camera node (today: a laptop webcam; later: an
    RTSP/IP CCTV camera). Location is configuration data, not code, so the
    same camera_code can be re-pointed at a new location_name/lat/lon
    without touching the ingestion pipeline."""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        OFFLINE = "OFFLINE", "Offline"

    class Direction(models.TextChoices):
        NORTH = "NORTH", "North"
        SOUTH = "SOUTH", "South"
        EAST = "EAST", "East"
        WEST = "WEST", "West"
        NORTHEAST = "NORTHEAST", "Northeast"
        NORTHWEST = "NORTHWEST", "Northwest"
        SOUTHEAST = "SOUTHEAST", "Southeast"
        SOUTHWEST = "SOUTHWEST", "Southwest"

    camera_code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    location_name = models.CharField(max_length=150)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    direction = models.CharField(max_length=10, choices=Direction.choices, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.INACTIVE)
    api_key = models.CharField(max_length=64, unique=True, default=generate_api_key, editable=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["camera_code"]

    def __str__(self) -> str:
        return f"{self.camera_code} - {self.name}"
