"""
URL configuration for BACnet Discovery - Simplified Core Version

Core URL patterns for device discovery and monitoring functionality.
Focused on essential BACnet operations without advanced analytics.
"""

from django.urls import path

from . import views
from .api_views import (
    DeviceStatusAPIView,
    DeviceTrendsAPIView,
)

app_name = "discovery"

urlpatterns = [
    # Core HTML views
    path("", views.dashboard, name="dashboard"),
    path("device/<int:device_id>/", views.device_detail, name="device_detail"),
    # Device discovery and management APIs
    path("api/start-discovery/", views.start_discovery, name="start_discovery"),
    path(
        "api/discover-points/<int:device_id>/",
        views.discover_device_points,
        name="discover_device_points",
    ),
    path("api/clear-devices/", views.clear_devices, name="clear_devices"),
    # Point reading APIs
    path(
        "api/read-values/<int:device_id>/",
        views.read_device_point_values,
        name="read_device_point_values",
    ),
    path(
        "api/read-point/<int:device_id>/<str:object_type>/" "<int:instance_number>/",
        views.read_single_point_value,
        name="read_single_point_value",
    ),
    path(
        "api/device-values/<int:device_id>/",
        views.get_device_value_api,
        name="get_device_value_api",
    ),
    # Device status and trends APIs (function-based)
    path(
        "api/devices/status/",
        views.devices_status_api,
        name="device_status_api",
    ),
    path(
        "api/devices/<int:device_id>/analytics/trends/",
        views.device_trends_api,
        name="device_trends_api",
    ),
    # Class-based API views (v2)
    path(
        "api/v2/devices/status/",
        DeviceStatusAPIView.as_view(),
        name="device-status-api-v2",
    ),
    path(
        "api/v2/devices/<int:device_id>/trends/",
        DeviceTrendsAPIView.as_view(),
        name="device-trends-api-v2",
    ),
]
