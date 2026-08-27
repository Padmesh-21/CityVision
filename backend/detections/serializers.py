from rest_framework import serializers

from vehicles.models import Vehicle, normalize_plate

from .models import Detection


class DetectionCreateSerializer(serializers.Serializer):
    """Validates the payload an edge camera node POSTs to /api/detections/.
    `camera_id` (the camera_code) is validated separately in the view
    against the API-key-authenticated camera -- see detections.views."""

    plate_number = serializers.CharField(max_length=15)
    ocr_confidence = serializers.FloatField(min_value=0.0, max_value=1.0)
    timestamp = serializers.DateTimeField()
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    direction = serializers.CharField(max_length=10, required=False, allow_blank=True, default="")
    vehicle_type = serializers.ChoiceField(choices=Vehicle.VehicleType.choices, required=False)
    plate_image = serializers.ImageField(required=False, allow_null=True)
    vehicle_image = serializers.ImageField(required=False, allow_null=True)

    def validate_plate_number(self, value: str) -> str:
        normalized = normalize_plate(value)
        if not normalized:
            raise serializers.ValidationError("Plate number is invalid after normalization.")
        return normalized


class DetectionSerializer(serializers.ModelSerializer):
    camera_code = serializers.CharField(source="camera.camera_code", read_only=True)
    location_name = serializers.CharField(source="camera.location_name", read_only=True)
    plate_number = serializers.CharField(source="vehicle.plate_number", read_only=True)

    class Meta:
        model = Detection
        fields = [
            "id",
            "camera",
            "camera_code",
            "location_name",
            "vehicle",
            "plate_number",
            "timestamp",
            "latitude",
            "longitude",
            "direction",
            "ocr_confidence",
            "plate_image",
            "vehicle_image",
            "processing_source",
            "created_at",
        ]
        read_only_fields = fields
