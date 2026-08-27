from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from vehicles.models import Vehicle, normalize_plate

from .serializers import TrajectorySerializer
from .services import get_vehicle_trajectory


class VehicleTrajectoryView(APIView):
    """GET /api/vehicles/<plate_number>/trajectory/

    Returns every detection of this plate across all cameras, ordered
    chronologically -- the vehicle's reconstructed movement across the
    city.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, plate_number: str):
        vehicle = get_object_or_404(Vehicle, plate_number=normalize_plate(plate_number))
        detections = get_vehicle_trajectory(vehicle)
        serializer = TrajectorySerializer(
            {"plate_number": vehicle.plate_number, "trajectory": detections}
        )
        return Response(serializer.data)
