from django.contrib import admin

from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ["plate_number", "vehicle_type", "first_seen", "last_seen"]
    list_filter = ["vehicle_type"]
    search_fields = ["plate_number"]
    readonly_fields = ["created_at", "updated_at"]
