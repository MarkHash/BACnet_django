from .models import BACnetDevice, BACnetPoint
from django.contrib import admin


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
