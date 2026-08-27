from django.urls import path

from .views import VehicleTrajectoryView

urlpatterns = [
    path("<str:plate_number>/trajectory/", VehicleTrajectoryView.as_view(), name="vehicle-trajectory"),
]
