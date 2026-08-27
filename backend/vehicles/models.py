import re

from django.db import models

# Strips spaces, hyphens and lowercases -> "TN 09 AB 1234" / "tn09ab1234"
# both collapse to the same stored value "TN09AB1234".
_PLATE_STRIP_RE = re.compile(r"[^A-Z0-9]")


def normalize_plate(raw: str) -> str:
    return _PLATE_STRIP_RE.sub("", raw.upper())


class Vehicle(models.Model):
    """One row per physical vehicle, identified by its normalized plate.
    A Vehicle is created the first time any camera reports its plate; every
    later detection just attaches to the existing row."""

    class VehicleType(models.TextChoices):
        CAR = "CAR", "Car"
        MOTORCYCLE = "MOTORCYCLE", "Motorcycle"
        TRUCK = "TRUCK", "Truck"
        BUS = "BUS", "Bus"
        AUTO = "AUTO", "Auto Rickshaw"
        UNKNOWN = "UNKNOWN", "Unknown"

    plate_number = models.CharField(max_length=15, unique=True, db_index=True)
    vehicle_type = models.CharField(
        max_length=20, choices=VehicleType.choices, default=VehicleType.UNKNOWN
    )
    first_seen = models.DateTimeField(null=True, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_seen"]

    def save(self, *args, **kwargs):
        if self.plate_number:
            self.plate_number = normalize_plate(self.plate_number)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.plate_number
