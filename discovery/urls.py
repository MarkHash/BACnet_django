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
    path("api/devices/", views.device_list_api, name="device_list_api"),
    # path("api/config/", views.config_info, name="config_info"),
    path("api/debug/", views.debug_urls, name="debug_urls"),
    path(
        "api/read-values/<int:device_id>/",
        views.read_point_values,
        name="read_point_values",
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
    path(
        "api/point-history/<int:point_id>/",
        views.get_point_history_api,
        name="get_point_history_api",
    ),
]
