from rest_framework import serializers

from .models import Camera


class CameraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Camera
        fields = [
            "id",
            "camera_code",
            "name",
            "location_name",
            "latitude",
            "longitude",
            "direction",
            "status",
            "last_seen",
            "created_at",
        ]
        read_only_fields = ["id", "last_seen", "created_at"]


class CameraAPIKeySerializer(serializers.ModelSerializer):
    """Only ever returned right after creation or a key regeneration --
    the API key is never included in CameraSerializer's list/retrieve
    output."""

    class Meta:
        model = Camera
        fields = ["id", "camera_code", "api_key"]
        read_only_fields = fields
