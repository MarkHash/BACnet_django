"""
URL configuration for bacnet_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path

from . import views
from .views import (
    DataQualityAPIView,
    DevicePerformanceAPIView,
    DeviceStatusAPIView,
    DeviceTrendsAPIView,
)

app_name = "discovery"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("device/<int:device_id>/", views.device_detail, name="device_detail"),
    path("api/start-discovery/", views.start_discovery, name="start_discovery"),
    path(
        "api/discover-points/<int:device_id>/",
        views.discover_device_points,
        name="discover_device_points",
    ),
    path("api/clear-devices/", views.clear_devices, name="clear_devices"),
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
    path("api/devices/status/", views.devices_status_api, name="device_status_api"),
    path(
        "api/devices/<int:device_id>/analytics/trends/",
        views.device_trends_api,
        name="device_trends_api",
    ),
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
    path(
        "api/v2/devices/performance/",
        DevicePerformanceAPIView.as_view(),
        name="device-performance-api",
    ),
    path(
        "api/v2/devices/data-quality/",
        DataQualityAPIView.as_view(),
        name="device-data-quality-api",
    ),
]
