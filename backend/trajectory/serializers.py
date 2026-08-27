from rest_framework import serializers


class TrajectoryPointSerializer(serializers.Serializer):
    camera = serializers.CharField(source="camera.camera_code")
    location = serializers.CharField(source="camera.location_name")
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    timestamp = serializers.DateTimeField()
    direction = serializers.CharField()
    confidence = serializers.FloatField(source="ocr_confidence")


class TrajectorySerializer(serializers.Serializer):
    plate_number = serializers.CharField()
    trajectory = TrajectoryPointSerializer(many=True)
