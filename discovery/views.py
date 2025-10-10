"""
BACnet Web Views - Simplified Core Version

This module provides basic web interface for BACnet device discovery and
monitoring. Focused on core functionality: device discovery, point reading,
and basic dashboards.

Core Features:
- Device discovery and management
- Point value reading and monitoring
- Simple dashboard interface
- Manual operations (discovery, clear devices)
- RESTful JSON API endpoints
"""

import logging
from typing import Any, Dict, List

from django.apps import apps
from django.contrib import messages
from django.db.models import Count
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .exceptions import (
    BACnetError,
    ConfigurationError,
    DeviceNotFoundError,
)
from .forms import VirtualDeviceCreateForm
from .models import (
    BACnetDevice,
    BACnetPoint,
)

# Legacy BACnetService import removed - using unified service
from .virtual_device_service import VirtualDeviceService


def create_error_response(error: Exception, user_friendly: bool = True) -> JsonResponse:
    if isinstance(error, DeviceNotFoundError):
        message = f"Device {error.device_id} not found"
    elif isinstance(error, ConfigurationError):
        message = "Configuration error - check BACpypes.ini file"
    elif isinstance(error, BACnetError):
        message = "BACnet communication error"
    else:
        message = "An unexpected error occurred"

    logger.error(f"API Error: {error}")
    return JsonResponse(
        {
            "success": False,
            "message": message,
            "error_type": error.__class__.__name__,
        }
    )


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def dashboard(request: HttpRequest) -> HttpResponse:
    devices = (
        BACnetDevice.objects.filter(is_active=True)
        .annotate(point_count=Count("points"))
        .order_by("-last_seen")
    )

    context = {
        "devices": devices,
        "total_devices": devices.count(),
        "online_devices": devices.filter(is_online=True).count(),
        "offline_devices": devices.filter(is_online=False).count(),
        "total_points": BACnetPoint.objects.count(),
    }
    return render(request, "discovery/dashboard.html", context)


def device_detail(request: HttpRequest, device_id: int) -> HttpResponse:
    device = get_object_or_404(BACnetDevice, device_id=device_id)
    points = device.points.all().order_by("object_type", "instance_number")

    points_by_type = _organise_points_by_type(points)
    context = _build_device_context(device, points, points_by_type)

    return render(request, "discovery/device_detail.html", context)


def _organise_points_by_type(points) -> Dict[str, List]:
    points_by_type = {}
    for point in points:
        if point.object_type not in points_by_type:
            points_by_type[point.object_type] = []
        points_by_type[point.object_type].append(point)
    return points_by_type


def _build_device_context(
    device: BACnetDevice, points, points_by_type: Dict
) -> Dict[str, Any]:
    context = {
        "device": device,
        "points": points,
        "points_by_type": points_by_type,
        "point_count": points.count(),
        "points_loaded_recently": device.points_read and points.exists(),
    }
    return context


@csrf_exempt
def read_device_point_values(request: HttpRequest, device_id: int) -> JsonResponse:
    if request.method == "POST":
        try:
            device = get_object_or_404(BACnetDevice, device_id=device_id)
            logger.debug(f"device_ID: {device.device_id}")

            # Use unified service
            discovery_app = apps.get_app_config("discovery")
            service = discovery_app.bacnet_service

            results = service._initialise_results()
            if service._connect():
                try:
                    service.read_device_points(device, results)
                    results["devices_processed"] = 1
                finally:
                    service._disconnect()

            return JsonResponse(
                {
                    "success": True,
                    "message": (
                        f"Read {results['readings_collected']} sensor values "
                        f"from device {device_id}"
                    ),
                    "readings_collected": results["readings_collected"],
                }
            )
        except Exception as e:
            logger.error(f"Error: {e}")
            return JsonResponse({"success": False, "message": str(e)})

    return JsonResponse({"success": False, "message": "Invalid request"})


@csrf_exempt
def discover_device_points(request: HttpRequest, device_id: int) -> JsonResponse:
    if request.method == "POST":
        try:
            device = get_object_or_404(BACnetDevice, device_id=device_id)
            logger.debug(f"device_ID: {device.device_id}")

            # Use unified service
            discovery_app = apps.get_app_config("discovery")
            service = discovery_app.bacnet_service
            point_list = service.discover_device_points(device)

            if point_list is not None:
                return JsonResponse(
                    {
                        "success": True,
                        "message": f"Discovered {len(point_list)} points for"
                        f" device {device.device_id}",
                        "device_id": device.device_id,
                        "estimated_time": "5-10 seconds",
                        "status": "reading",
                    }
                )
            else:
                return JsonResponse(
                    {
                        "success": False,
                        "message": f"Failed to discover points for "
                        f"device {device.device_id}",
                        "device_id": device.device_id,
                    }
                )
        except Exception as e:
            logger.error(f"Error: {e}")
            return JsonResponse({"success": False, "message": str(e)})

    return JsonResponse({"success": False, "message": "Invalid request"})


@csrf_exempt
def start_discovery(request: HttpRequest) -> JsonResponse:
    if request.method == "POST":
        try:
            discovery_app = apps.get_app_config("discovery")
            bacnet_service = discovery_app.bacnet_service

            devices = bacnet_service.discover_devices()

            # Convert to legacy format for API compatibility
            legacy_devices = []
            for device in devices:
                legacy_devices.append(
                    {
                        "deviceId": device["device_id"],
                        "address": device["ip_address"],
                        "vendorId": 842,  # Default BAC0 vendor ID
                    }
                )

            return JsonResponse(
                {
                    "success": True,
                    "message": f"Found {len(devices)} devices",
                    "devices": legacy_devices,
                }
            )
        except Exception as e:
            return JsonResponse(
                {
                    "success": False,
                    "message": f"Discovery failed: {str(e)}",
                }
            )

    return JsonResponse({"success": False, "message": "Invalid request"})


@csrf_exempt
def read_single_point_value(
    request: HttpRequest,
    device_id: int,
    object_type: str,
    instance_number: int,
) -> JsonResponse:
    if request.method == "POST":
        try:
            device = get_object_or_404(BACnetDevice, device_id=device_id)
            point = get_object_or_404(
                BACnetPoint,
                device=device,
                object_type=object_type,
                instance_number=instance_number,
            )
            # Use unified service
            discovery_app = apps.get_app_config("discovery")
            service = discovery_app.bacnet_service
            value = service.read_point_value(device, point)

            return JsonResponse(
                {
                    "success": True,
                    "message": f"Reading values from "
                    f"{object_type}:{instance_number}",
                    "value": value,
                    "point_id": point.id,
                }
            )

        except Exception as e:
            logger.error(f"Error: {e}")
            return JsonResponse({"success": False, "message": str(e)})

    return JsonResponse({"success": False, "message": "Invalid request"})


def get_device_value_api(request: HttpRequest, device_id: int) -> JsonResponse:
    device = get_object_or_404(BACnetDevice, device_id=device_id)
    points_data = []
    for point in device.points.all().order_by("object_type", "instance_number"):
        point_data = {
            "id": point.id,
            "identifier": point.identifier,
            "object_type": point.object_type,
            "instance_number": point.instance_number,
            "object_name": point.object_name or "",
            "present_value": point.present_value or "",
            "units": point.units or "",
            "display_value": point.get_display_value(),
            "value_last_read": (
                point.value_last_read.isoformat() if point.value_last_read else None
            ),
            "is_readable": point.is_readable,
            "data_type": point.data_type or "",
        }
        points_data.append(point_data)

    return JsonResponse(
        {
            "success": True,
            "device_id": device.device_id,
            "points": points_data,
            "total_points": len(points_data),
            "readable_points": len([p for p in points_data if p["is_readable"]]),
            "last_updated": timezone.now().isoformat(),
        }
    )


@csrf_exempt
def clear_devices(request: HttpRequest) -> JsonResponse:
    if request.method == "POST":
        try:
            device_count = BACnetDevice.objects.filter(is_active=True).count()
            point_count = BACnetPoint.objects.filter(device__is_active=True).count()

            BACnetDevice.objects.filter(is_active=True).update(
                is_active=False, deactivated_at=timezone.now()
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": f"Cleared {device_count} devices and"
                    f" {point_count} points",
                }
            )
        except Exception as e:
            return JsonResponse(
                {
                    "success": False,
                    "message": f"Error clearing devices: {str(e)}",
                }
            )

    return JsonResponse({"success": False, "message": "Invalid request"})


def virtual_device_list(request: HttpRequest) -> HttpResponse:
    """List all virtual devices"""
    devices = VirtualDeviceService.get_all_devices()

    context = {
        "virtual_devices": devices,
        "total_devices": devices.count(),
        "running_devices": devices.filter(is_running=True).count(),
    }

    return render(request, "discovery/virtual_device_list.html", context)


def virtual_device_create(request: HttpRequest) -> HttpResponse:
    """Create new virtual device"""
    if request.method == "POST":
        form = VirtualDeviceCreateForm(request.POST)
        if form.is_valid():
            try:
                device = VirtualDeviceService.create_virtual_device(
                    device_id=form.cleaned_data["device_id"],
                    device_name=form.cleaned_data["device_name"],
                    description=form.cleaned_data.get("description", ""),
                    port=form.cleaned_data.get("port", 47808),
                )

                messages.success(
                    request,
                    f"Virtual device {device.device_id} created successfully! "
                    f"It will start within 5 seconds if the server is running.",
                )
                return redirect("discovery:virtual_device_list")

            except ValueError as e:
                messages.error(request, str(e))

    else:
        form = VirtualDeviceCreateForm()

    context = {"form": form}
    return render(request, "discovery/virtual_device_create.html", context)


@csrf_exempt
def virtual_device_delete(request: HttpRequest, device_id: int) -> JsonResponse:
    """Delete virtual device"""
    if request.method == "POST":
        success = VirtualDeviceService.delete_virtual_device(device_id)

        if success:
            return JsonResponse(
                {
                    "success": True,
                    "message": f"Virtual device {device_id} deleted successfully",
                }
            )
        else:
            return JsonResponse(
                {"success": False, "message": f"Virtual device {device_id} not found"},
                status=404,
            )
    return JsonResponse(
        {"success": False, "message": "Invalid request method"}, status=400
    )
