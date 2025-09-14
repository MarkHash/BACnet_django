import json
import logging
import os
import sys
import threading
import time

from bacpypes.consolelogging import ConfigArgumentParser
from bacpypes.core import enable_sleeping, run
from bacpypes.local.device import LocalDeviceObject
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .bacnet_client import DjangoBACnetClient, clear_all_devices
from .constants import BACnetConstants
from .decorators import requires_client_only, requires_device_and_client
from .exceptions import (
    BACnetError,
    ConfigurationError,
    DeviceNotFoundByAddressError,
    DeviceNotFoundError,
    PointNotFoundError,
)
from .models import BACnetDevice, BACnetPoint


def create_error_response(error, user_friendly=True):
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


# Create your views here.
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

bacnet_client = None
bacnet_config = None


def load_bacnet_config():
    global bacnet_config
    if bacnet_config is None:
        try:
            logger.debug("Loading BACnet configuration from BACpypes.ini...")
            original_argv = sys.argv.copy()
            ini_path = "./discovery/BACpypes.ini"
            if not os.path.exists(ini_path):
                raise ConfigurationError(
                    "Failed to load BACpypes.ini",
                    config_file="./discovery/BACpypes.ini",
                )

            sys.argv = ["django_bacnet", "--ini", ini_path]
            args = ConfigArgumentParser(
                description="Django BACnet Discovery"
            ).parse_args()
            bacnet_config = args.ini
            sys.argv = original_argv

            logger.debug("✅ Configuration loaded:")
            logger.debug(f"   Device Name: {bacnet_config}")

        except Exception as e:
            logger.debug(f"Error loading BACnet configuration: {e}")
            sys.argv = original_argv
            bacnet_config = None

    return bacnet_config


def dashboard(request):
    devices = (
        BACnetDevice.objects.all()
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


def device_detail(request, device_id):
    device = get_object_or_404(BACnetDevice, device_id=device_id)
    points = device.points.all().order_by("object_type", "instance_number")

    if points.exists() and device.points_read:
        try:
            client = ensure_bacnet_client()
            if client:
                latest_reading = points.filter(value_last_read__isnull=False).first()
                if (
                    not latest_reading
                    or (timezone.now() - latest_reading.value_last_read).total_seconds()
                    > BACnetConstants.REFRESH_THRESHOLD_SECONDS
                ):
                    client.read_all_point_values(device.device_id)
                    logger.debug(
                        f"Triggered point value reading for device {device.device_id}"
                    )

        except Exception as e:
            logger.error(f"Error triggering point value reading: {e}")

    points_by_type = {}
    for point in points:
        if point.object_type not in points_by_type:
            points_by_type[point.object_type] = []
        points_by_type[point.object_type].append(point)

    context = {
        "device": device,
        "points": points,
        "points_by_type": points_by_type,
        "point_count": points.count(),
        "points_loaded_recently": device.points_read and points.exists(),
    }
    return render(request, "discovery/device_detail.html", context)


def ensure_bacnet_client():
    global bacnet_client

    if bacnet_client is None:
        logger.debug("🔧 Creating BACnet client...")

        # args = ConfigArgumentParser(description=__doc__).parse_args()
        config = load_bacnet_config()
        if config is None:
            raise ConfigurationError(
                "Could not load BACnet configuration from BACpypes.ini"
            )

        device = LocalDeviceObject(
            objectName=config.objectname,
            objectIdentifier=int(config.objectidentifier),
            maxApduLengthAccepted=int(config.maxapdulengthaccepted),
            segmentationSupported=config.segmentationsupported,
            vendorIdentifier=int(config.vendoridentifier),
        )
        logger.debug(f"📡 Creating BACnet client with address: {config.address}")

        def callback(event_type, data):
            logger.debug(f"BACnet event: {event_type} - {data}")

        bacnet_client = DjangoBACnetClient(callback, device, config.address)

        def run_bacnet():
            enable_sleeping()
            run()

        bacnet_thread = threading.Thread(target=run_bacnet, daemon=True)
        bacnet_thread.start()

        logger.debug("✅ BACnet client started!")
    return bacnet_client


@csrf_exempt
@requires_client_only
def start_discovery(request, client):
    if request.method == "POST":
        logger.debug("ensure_bacnet_client")
        client.send_whois()

        return JsonResponse(
            {
                "success": True,
                "message": f"Device discovery started"
                f" - devices will appear in a few seconds",
            }
        )

    return JsonResponse({"success": False, "message": "Invalid request"})


@csrf_exempt
@requires_device_and_client
def read_device_points(request, device_id, device, client):
    if request.method == "POST":
        logger.debug(f"device_ID: {device_id}")
        client.read_device_objects(device.device_id)

        return JsonResponse(
            {
                "success": True,
                "message": f"Started reading points for device {device.device_id}",
                "device_id": device.device_id,
                "estimated_time": "5-10 seconds",
                "status": "reading",
            }
        )

    return JsonResponse({"success": False, "message": "Invalid request"})


@csrf_exempt
@requires_device_and_client
def read_point_values(request, device_id, device, client):
    if request.method == "POST":
        client.read_all_point_values(device.device_id)

        return JsonResponse(
            {
                "success": True,
                "message": f"Started reading sensor values for device {device.device_id}",
            }
        )

    return JsonResponse({"success": False, "message": "Invalid request"})


@csrf_exempt
@requires_device_and_client
def read_single_point_value(
    request, device_id, device, client, object_type, instance_number
):
    if request.method == "POST":
        client.read_point_value(device_id, object_type, instance_number)

        return JsonResponse(
            {
                "success": True,
                "message": f"Reading values from {object_type}:{instance_number}",
            }
        )

    return JsonResponse({"success": False, "message": "Invalid request"})


@requires_device_and_client
def get_device_value_api(request, device_id, device, client):
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


def get_point_history_api(request, point_id):
    try:
        point = get_object_or_404(BACnetPoint, id=point_id)

        readings = point.readings.all()[: BACnetConstants.MAX_READING_LIMIT]
        readings_data = []

        for reading in readings:
            readings_data.append(
                {
                    "value": reading.value,
                    "units": reading.units,
                    "display_value": reading.get_display_value(),
                    "read_time": reading.read_time.isoformat(),
                    "quality": reading.quality or "unknown",
                }
            )

        return JsonResponse(
            {
                "success": True,
                "point": {
                    "id": point.id,
                    "identifier": point.identifier,
                    "object_name": point.object_name,
                    "current_value": point.get_display_value(),
                },
                "readings": readings_data,
                "count": len(readings_data),
            }
        )
    except Exception as e:
        return JsonResponse(
            {"success": False, "message": f"Error getting point history: {str(e)}"}
        )


@csrf_exempt
def clear_devices(request):
    if request.method == "POST":
        try:
            device_count, point_count = clear_all_devices()

            return JsonResponse(
                {
                    "success": True,
                    "message": f"Cleared {device_count} devices and {point_count} points",
                }
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"Error clearing devices: {str(e)}"}
            )

    return JsonResponse({"success": False, "message": "Invalid request"})


def device_list_api(request):
    devices = BACnetDevice.objects.all().values(
        "device_id", "address", "vendor_id", "is_online", "last_seen", "points_read"
    )

    return JsonResponse({"devices": list(devices), "count": len(devices)})


def debug_urls(request):
    urls = {
        "dashboard": reverse("discovery:dashboard"),
        "device_detail_example": "/device/123123",
        "start_discovery": reverse("discovery:start_discovery"),
        "clear_devices": reverse("discovery:clear_devices"),
        "device_list_api": reverse("discovery:device_list_api"),
    }

    try:
        device = BACnetDevice.objects.first()
        if device:
            urls["device_detail_real"] = reverse(
                "discovery:device_detail", args=[device.device_id]
            )
            urls["read_points_real"] = reverse(
                "discovery:read_device_points", args=[device.device_id]
            )
        else:
            urls["read_points_example"] = "/api/read-points/123123/"
    except:
        urls["read_points_example"] = "/api/read-points/123123"

    return JsonResponse(
        {"available_urls": urls, "method": request.method, "path": request.path}
    )


def config_info(request):
    config = load_bacnet_config()
    if config:
        config_data = {
            "device_name": config.name,
            "device_id": config.instance,
            "address": config.address,
            "vendor_id": config.vendorid,
            "max_apdu_length": config.maxpdulength,
            "segmentation": config.segmentation,
        }
        return JsonResponse({"success": True, "config": config_data})
    else:
        return JsonResponse(
            {"success": False, "config": "Could not load BACnet configuration"}
        )
