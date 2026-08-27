from django.db import models

from detections.models import Detection
from vehicles.models import Vehicle, normalize_plate


class Blacklist(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        RESOLVED = "RESOLVED", "Resolved"

    plate_number = models.CharField(max_length=15, unique=True, db_index=True)
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Blacklist entries"

    def save(self, *args, **kwargs):
        if self.plate_number:
            self.plate_number = normalize_plate(self.plate_number)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.plate_number} ({self.status})"


class Alert(models.Model):
    class AlertType(models.TextChoices):
        BLACKLISTED_VEHICLE = "BLACKLISTED_VEHICLE", "Blacklisted Vehicle"
        ROUTE_ANOMALY = "ROUTE_ANOMALY", "Route Anomaly"
        LOW_CONFIDENCE = "LOW_CONFIDENCE", "Low Confidence"
        SYSTEM_ALERT = "SYSTEM_ALERT", "System Alert"

    class Severity(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"

    class Status(models.TextChoices):
        NEW = "NEW", "New"
        ACKNOWLEDGED = "ACKNOWLEDGED", "Acknowledged"
        RESOLVED = "RESOLVED", "Resolved"

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="alerts")
    detection = models.ForeignKey(
        Detection, on_delete=models.CASCADE, related_name="alerts", null=True, blank=True
    )
    alert_type = models.CharField(max_length=30, choices=AlertType.choices)
    message = models.CharField(max_length=255)
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.MEDIUM)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.alert_type} - {self.vehicle.plate_number}"
