from django.urls import path

from .views import AnalyticsSummaryView, AverageSpeedView, HeatmapView, RouteDensityView

urlpatterns = [
    path("summary/", AnalyticsSummaryView.as_view(), name="analytics-summary"),
    path("route-density/", RouteDensityView.as_view(), name="analytics-route-density"),
    path("average-speed/", AverageSpeedView.as_view(), name="analytics-average-speed"),
    path("heatmap/", HeatmapView.as_view(), name="analytics-heatmap"),
]
