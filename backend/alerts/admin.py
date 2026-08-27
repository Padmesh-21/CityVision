from django.contrib import admin

from .models import Alert, Blacklist


@admin.register(Blacklist)
class BlacklistAdmin(admin.ModelAdmin):
    list_display = ["plate_number", "reason", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["plate_number"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ["vehicle", "alert_type", "severity", "status", "created_at"]
    list_filter = ["alert_type", "severity", "status"]
    search_fields = ["vehicle__plate_number"]
    readonly_fields = ["created_at"]
