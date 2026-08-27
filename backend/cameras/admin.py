from django.contrib import admin

from .models import Camera


@admin.register(Camera)
class CameraAdmin(admin.ModelAdmin):
    list_display = ["camera_code", "name", "location_name", "status", "direction", "last_seen"]
    list_filter = ["status", "direction"]
    search_fields = ["camera_code", "name", "location_name"]
    readonly_fields = ["api_key", "last_seen", "created_at"]
