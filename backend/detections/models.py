from django.db import models

from cameras.models import Camera
from vehicles.models import Vehicle


def plate_image_upload_path(instance: "Detection", filename: str) -> str:
    return f"detections/plates/{instance.camera.camera_code}/{filename}"


def vehicle_image_upload_path(instance: "Detection", filename: str) -> str:
    return f"detections/vehicles/{instance.camera.camera_code}/{filename}"


class Detection(models.Model):
    """One vehicle-passage event at one camera. Trajectories, analytics
    and alerts are all derived from this table -- there is deliberately no
    separate trajectory table (see docs/database.md)."""

    class Source(models.TextChoices):
        EDGE = "EDGE", "Edge Node OCR"
        SERVER_VERIFIED = "SERVER_VERIFIED", "Server-Verified OCR"

    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name="detections")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="detections")
    timestamp = models.DateTimeField(db_index=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    direction = models.CharField(max_length=10, blank=True)
    ocr_confidence = models.FloatField()
    plate_image = models.ImageField(upload_to=plate_image_upload_path, null=True, blank=True)
    vehicle_image = models.ImageField(upload_to=vehicle_image_upload_path, null=True, blank=True)
    processing_source = models.CharField(max_length=20, choices=Source.choices, default=Source.EDGE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["vehicle", "timestamp"]),
            models.Index(fields=["camera", "timestamp"]),
        ]

    def __str__(self) -> str:
        return f"{self.vehicle.plate_number} @ {self.camera.camera_code} ({self.timestamp})"
