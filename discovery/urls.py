"""
URL configuration for BACnet Discovery

Core URL patterns for BACnet device discovery, point reading, and virtual
device management.
Focused on essential BACnet protocol operations using the unified service architecture.
"""

from django.urls import path

from . import views

app_name = "discovery"

urlpatterns = [
    # ==================== Web Views ====================
    path("", views.dashboard, name="dashboard"),
    path("device/<int:device_id>/", views.device_detail, name="device_detail"),
    # ==================== Device Discovery APIs ====================
    path("api/start-discovery/", views.start_discovery, name="start_discovery"),
    path("api/clear-devices/", views.clear_devices, name="clear_devices"),
    path(
        "api/discover-points/<int:device_id>/",
        views.discover_device_points,
        name="discover_device_points",
    ),
    # ==================== Point Reading APIs ====================
    path(
        "api/read-values/<int:device_id>/",
        views.read_device_point_values,
        name="read_device_point_values",
    ),
    path(
        "api/read-point/<int:device_id>/<str:object_type>/<int:instance_number>/",
        views.read_single_point_value,
        name="read_single_point_value",
    ),
    path(
        "api/device-values/<int:device_id>/",
        views.get_device_value_api,
        name="get_device_value_api",
    ),
    # ==================== Virtual Device Management ====================
    path(
        "virtual-devices/",
        views.virtual_device_list,
        name="virtual_device_list",
    ),
    path(
        "virtual-devices/create/",
        views.virtual_device_create,
        name="virtual_device_create",
    ),
    path(
        "api/virtual-devices/<int:device_id>/delete/",
        views.virtual_device_delete,
        name="virtual_device_delete",
    ),
]
