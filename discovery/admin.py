from django.contrib import admin

from .models import (
    AlarmHistory,
    BACnetDevice,
    BACnetPoint,
    BACnetReading,
    DeviceStatusHistory,
    MaintenanceLog,
    SensorReadingStats,
)


# Register your models here.
@admin.register(BACnetDevice)
class BACnetDeviceAdmin(admin.ModelAdmin):
    list_display = [
        "device_id",
        "address",
        "vendor_id",
        "is_online",
        "points_read",
        "last_seen",
    ]
    list_filter = ["is_online", "points_read", "vendor_id"]
    search_fields = ["device_id", "address"]
    readonly_fields = ["first_seen", "last_seen"]

    class BACnetPointInline(admin.TabularInline):
        model = BACnetPoint
        extra = 0
        readonly_fields = ["created"]

    inlines = [BACnetPointInline]


@admin.register(BACnetPoint)
class BACnetPointAdmin(admin.ModelAdmin):
    list_display = ["identifier", "device", "object_type", "instance_number", "created"]
    list_filter = ["object_type", "device"]
    search_fields = ["identifier", "object_name", "description"]
    readonly_fields = ["created"]

    fieldsets = (
        (
            "Point Identification",
            {"fields": ("device", "object_type", "instance_number", "identifier")},
        ),
        (
            "Additional Information",
            {"fields": ("object_name", "description"), "classes": ("collapse",)},
        ),
        ("Timestamps", {"fields": ("created",), "classes": ("collapse",)}),
    )


@admin.register(BACnetReading)
class BACnetReadingAdmin(admin.ModelAdmin):
    list_display = ["point", "value", "read_time", "is_anomaly", "data_quality_score"]
    list_filter = ["is_anomaly", "read_time", "point__device"]
    search_fields = ["point__identifier", "value"]
    readonly_fields = ["read_time"]
    date_hierarchy = "read_time"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("point__device")


admin.site.register(DeviceStatusHistory)
admin.site.register(SensorReadingStats)
admin.site.register(AlarmHistory)
admin.site.register(MaintenanceLog)
