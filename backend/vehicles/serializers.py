from rest_framework import serializers

from .models import Vehicle


class VehicleSerializer(serializers.ModelSerializer):
    total_detections = serializers.IntegerField(source="detections.count", read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            "id",
            "plate_number",
            "vehicle_type",
            "first_seen",
            "last_seen",
            "total_detections",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
