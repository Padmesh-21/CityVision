from django.contrib import admin

from .models import Detection


@admin.register(Detection)
class DetectionAdmin(admin.ModelAdmin):
    list_display = ["vehicle", "camera", "timestamp", "ocr_confidence", "processing_source"]
    list_filter = ["camera", "processing_source"]
    search_fields = ["vehicle__plate_number", "camera__camera_code"]
    date_hierarchy = "timestamp"
    readonly_fields = ["created_at"]
