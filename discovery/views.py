import logging

from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .constants import BACnetConstants
from .exceptions import BACnetError, ConfigurationError, DeviceNotFoundError
from .models import BACnetDevice, BACnetPoint

# from .bacnet_client import DjangoBACnetClient, clear_all_devices
from .services import BACnetService


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


logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def dashboard(request):
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


def device_detail(request, device_id):
    device = get_object_or_404(BACnetDevice, device_id=device_id)
    points = device.points.all().order_by("object_type", "instance_number")

    points_by_type = _organise_points_by_type(points)
    context = _build_device_context(device, points, points_by_type)

    return render(request, "discovery/device_detail.html", context)


def _should_refresh_readings(latest_reading):
    if not latest_reading:
        return True
    time_since_reading = (
        timezone.now() - latest_reading.value_last_read
    ).total_seconds()
    return time_since_reading > BACnetConstants.REFRESH_THRESHOLD_SECONDS


def _organise_points_by_type(points):
    points_by_type = {}
    for point in points:
        if point.object_type not in points_by_type:
            points_by_type[point.object_type] = []
        points_by_type[point.object_type].append(point)
    return points_by_type


def _build_device_context(device, points, points_by_type):
    context = {
        "device": device,
        "points": points,
        "points_by_type": points_by_type,
        "point_count": points.count(),
        "points_loaded_recently": device.points_read and points.exists(),
    }
    return context


@csrf_exempt
def read_device_point_values(request, device_id):
    if request.method == "POST":
        try:
            device = get_object_or_404(BACnetDevice, device_id=device_id)
            logger.debug(f"device_ID: {device.device_id}")
            service = BACnetService()

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
def discover_device_points(request, device_id):
    if request.method == "POST":
        try:
            device = get_object_or_404(BACnetDevice, device_id=device_id)
            logger.debug(f"device_ID: {device.device_id}")
            service = BACnetService()
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
def start_discovery(request):
    if request.method == "POST":
        try:
            logger.debug("ensure_bacnet_client")
            service = BACnetService()
            devices = service.discover_devices()

            if devices is not None:
                return JsonResponse(
                    {
                        "success": True,
                        "message": f"Device discovery completed with"
                        f" {len(devices)} devices",
                    }
                )
            else:
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Device discovery failed",
                    }
                )
        except Exception as e:
            logger.error(f"Error: {e}")
            return JsonResponse({"success": False, "message": str(e)})

    return JsonResponse({"success": False, "message": "Invalid request"})


# @csrf_exempt
# def read_point_values(request):
#     if request.method == "POST":
#         try:
#             service = BACnetService()
#             result = service.collect_all_readings()

#             return JsonResponse(
#                 {
#                     "success": True,
#                     "message": f"Read {result['readings_collected']} sensor values",
#                 }
#             )
#         except Exception as e:
#             logger.error(f"Error: {e}")
#             return JsonResponse({"success": False, "message": str(e)})

#     return JsonResponse({"success": False, "message": "Invalid request"})


@csrf_exempt
def read_single_point_value(request, device_id, object_type, instance_number):
    if request.method == "POST":
        try:
            device = get_object_or_404(BACnetDevice, device_id=device_id)
            point = get_object_or_404(
                BACnetPoint,
                device=device,
                object_type=object_type,
                instance_number=instance_number,
            )
            service = BACnetService()
            value = service.read_point_value(device, point)

            return JsonResponse(
                {
                    "success": True,
                    "message": f"Reading values from {object_type}:{instance_number}",
                    "value": value,
                    "point_id": point.id,
                }
            )

        except Exception as e:
            logger.error(f"Error: {e}")
            return JsonResponse({"success": False, "message": str(e)})

    return JsonResponse({"success": False, "message": "Invalid request"})


def get_device_value_api(request, device_id):
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


# def get_point_history_api(request, point_id):
#     try:
#         point = get_object_or_404(BACnetPoint, id=point_id)

#         readings = point.readings.all()[: BACnetConstants.MAX_READING_LIMIT]
#         readings_data = []

#         for reading in readings:
#             readings_data.append(
#                 {
#                     "value": reading.value,
#                     "units": reading.units,
#                     "display_value": reading.get_display_value(),
#                     "read_time": reading.read_time.isoformat(),
#                     "quality": reading.quality or "unknown",
#                 }
#             )

#         return JsonResponse(
#             {
#                 "success": True,
#                 "point": {
#                     "id": point.id,
#                     "identifier": point.identifier,
#                     "object_name": point.object_name,
#                     "current_value": point.get_display_value(),
#                 },
#                 "readings": readings_data,
#                 "count": len(readings_data),
#             }
#         )
#     except Exception as e:
#         return JsonResponse(
#             {"success": False, "message": f"Error getting point history: {str(e)}"}
#         )


@csrf_exempt
def clear_devices(request):
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
                {"success": False, "message": f"Error clearing devices: {str(e)}"}
            )

    return JsonResponse({"success": False, "message": "Invalid request"})
