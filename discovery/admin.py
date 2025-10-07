from django.contrib import admin

from .models import (
    BACnetDevice,
    BACnetPoint,
    BACnetReading,
    DeviceStatusHistory,
    VirtualBACnetDevice,
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
    list_display = [
        "identifier",
        "device",
        "object_type",
        "instance_number",
        "created",
    ]
    list_filter = ["object_type", "device"]
    search_fields = ["identifier", "object_name", "description"]
    readonly_fields = ["created"]

    fieldsets = (
        (
            "Point Identification",
            {
                "fields": (
                    "device",
                    "object_type",
                    "instance_number",
                    "identifier",
                )
            },
        ),
        (
            "Additional Information",
            {
                "fields": ("object_name", "description"),
                "classes": ("collapse",),
            },
        ),
        ("Timestamps", {"fields": ("created",), "classes": ("collapse",)}),
    )


@admin.register(BACnetReading)
class BACnetReadingAdmin(admin.ModelAdmin):
    list_display = ["point", "value", "read_time"]
    list_filter = ["read_time", "point__device"]
    search_fields = ["point__identifier", "value"]
    readonly_fields = ["read_time"]
    date_hierarchy = "read_time"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("point__device")


@admin.register(VirtualBACnetDevice)
class VirtualBACnetDeviceAdmin(admin.ModelAdmin):
    list_display = ["device_id", "device_name", "port", "is_running", "created_at"]
    list_filter = ["is_running"]
    search_fields = ["device_id", "device_name"]


admin.site.register(DeviceStatusHistory)
