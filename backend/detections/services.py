"""Business logic for turning a validated detection payload into database
rows. Kept out of views.py so the API layer stays thin and this logic is
reusable (e.g. from a management command or a future Celery task)."""

import logging

from django.utils import timezone

from alerts.models import Alert, Blacklist
from cameras.models import Camera
from vehicles.models import Vehicle

from .models import Detection

logger = logging.getLogger(__name__)


def process_detection(camera: Camera, data: dict) -> tuple[Detection, bool]:
    """
    Detection
       -> find/create Vehicle
       -> create Detection
       -> update Vehicle.first_seen/last_seen
       -> update Camera.last_seen
       -> check Blacklist -> create Alert if matched

    Returns (detection, alert_generated).
    """
    plate_number = data["plate_number"]
    timestamp = data["timestamp"]

    vehicle, created = Vehicle.objects.get_or_create(
        plate_number=plate_number,
        defaults={
            "vehicle_type": data.get("vehicle_type", Vehicle.VehicleType.UNKNOWN),
            "first_seen": timestamp,
            "last_seen": timestamp,
        },
    )
    if created:
        logger.info("New vehicle registered: %s", plate_number)

    detection = Detection.objects.create(
        camera=camera,
        vehicle=vehicle,
        timestamp=timestamp,
        latitude=data["latitude"],
        longitude=data["longitude"],
        direction=data.get("direction", ""),
        ocr_confidence=data["ocr_confidence"],
        plate_image=data.get("plate_image"),
        vehicle_image=data.get("vehicle_image"),
    )

    vehicle_updates = []
    if vehicle.first_seen is None or timestamp < vehicle.first_seen:
        vehicle.first_seen = timestamp
        vehicle_updates.append("first_seen")
    if vehicle.last_seen is None or timestamp > vehicle.last_seen:
        vehicle.last_seen = timestamp
        vehicle_updates.append("last_seen")
    if data.get("vehicle_type") and vehicle.vehicle_type == Vehicle.VehicleType.UNKNOWN:
        vehicle.vehicle_type = data["vehicle_type"]
        vehicle_updates.append("vehicle_type")
    if vehicle_updates:
        vehicle.save(update_fields=vehicle_updates)

    camera.last_seen = timezone.now()
    camera.save(update_fields=["last_seen"])

    alert_generated = _check_blacklist_and_alert(vehicle, detection, camera)

    return detection, alert_generated


def _check_blacklist_and_alert(vehicle: Vehicle, detection: Detection, camera: Camera) -> bool:
    match = Blacklist.objects.filter(
        plate_number=vehicle.plate_number, status=Blacklist.Status.ACTIVE
    ).first()
    if not match:
        return False

    Alert.objects.create(
        vehicle=vehicle,
        detection=detection,
        alert_type=Alert.AlertType.BLACKLISTED_VEHICLE,
        message=f"Blacklisted vehicle {vehicle.plate_number} detected at {camera.camera_code} "
        f"({camera.location_name}): {match.reason}",
        severity=Alert.Severity.CRITICAL,
    )
    logger.warning("ALERT: blacklisted plate %s seen at %s", vehicle.plate_number, camera.camera_code)
    # Step 8 will broadcast this over a WebSocket to the React dashboard.
    return True
