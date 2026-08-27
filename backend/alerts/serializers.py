from rest_framework import serializers

from .models import Alert, Blacklist


class BlacklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blacklist
        fields = ["id", "plate_number", "reason", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class AlertSerializer(serializers.ModelSerializer):
    plate_number = serializers.CharField(source="vehicle.plate_number", read_only=True)
    camera_code = serializers.SerializerMethodField()
    location_name = serializers.SerializerMethodField()

    class Meta:
        model = Alert
        fields = [
            "id",
            "vehicle",
            "plate_number",
            "detection",
            "camera_code",
            "location_name",
            "alert_type",
            "message",
            "severity",
            "status",
            "created_at",
            "resolved_at",
        ]
        read_only_fields = fields

    def get_camera_code(self, obj: Alert):
        return obj.detection.camera.camera_code if obj.detection else None

    def get_location_name(self, obj: Alert):
        return obj.detection.camera.location_name if obj.detection else None
