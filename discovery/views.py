import logging
from datetime import timedelta

from django.db.models import Avg, Count, FloatField, Max, Min
from django.db.models.functions import Cast
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .constants import BACnetConstants
from .decorators import api_error_handler, api_rate_limit
from .exceptions import (
    BACnetError,
    ConfigurationError,
    DeviceNotFoundAPIError,
    DeviceNotFoundError,
    ValidationError,
)
from .models import BACnetDevice, BACnetPoint
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


@api_rate_limit(rate="200/h", method=["GET", "POST"])
@api_error_handler
@csrf_exempt
def devices_status_api(request):
    """
    GET /api/devices/status/ - All devices overview
    """

    try:
        device_info = []
        active_devices = BACnetDevice.objects.filter(is_active=True)
        for device in active_devices:
            device_status = "online"
            total_points = device.points.count()
            if device.last_seen:
                time_since_reading = (timezone.now() - device.last_seen).total_seconds()
            else:
                time_since_reading = 365 * 24 * 60 * 60

            if device.is_online is True:
                if total_points == 0:
                    device_status = "no_data"
                elif time_since_reading > BACnetConstants.STALE_THRESHOLD_SECONDS:
                    device_status = "stale"
            else:
                if time_since_reading > (7 * 24 * 60 * 60):
                    continue
                device_status = "offline"

            all_points = device.points.all()
            readable_points = len([p for p in all_points if p.is_readable])
            points_with_values = device.points.filter(
                present_value__isnull=False
            ).count()

            device_info.append(
                {
                    "device_id": device.device_id,
                    "address": device.address,
                    "statistics": {
                        "total_points": total_points,
                        "readable_points": readable_points,
                        "points_with_values": points_with_values,
                        "device_status": device_status,
                        "last_reading_time": device.last_seen,
                    },
                }
            )
        return JsonResponse(
            {
                "success": True,
                "summary": {
                    "total_devices": len(device_info),
                    "online_devices": len(
                        [
                            d
                            for d in device_info
                            if d["statistics"]["device_status"] == "online"
                        ]
                    ),
                    "offline_devices": len(
                        [
                            d
                            for d in device_info
                            if d["statistics"]["device_status"] == "offline"
                        ]
                    ),
                    "stale_devices": len(
                        [
                            d
                            for d in device_info
                            if d["statistics"]["device_status"] == "stale"
                        ]
                    ),
                    "no_data_devices": len(
                        [
                            d
                            for d in device_info
                            if d["statistics"]["device_status"] == "no_data"
                        ]
                    ),
                },
                "devices": device_info,
                "timestamp": timezone.now().isoformat(),
            }
        )
    except Http404:
        raise DeviceNotFoundAPIError()


@api_rate_limit(rate="100/h", method=["GET", "POST"])
@api_error_handler
def device_trends_api(request, device_id):
    """
    GET /api/devices/{id}/analytics/trends/
    ?period=24hours&points=analogInput:100,analogInput:101
    Returns historical data trends for specific device points
    """

    try:
        device = get_object_or_404(BACnetDevice, device_id=device_id)
        all_points = device.points.all()
        period = request.GET.get("period", "24hours")
        if period not in BACnetConstants.PERIOD_PARAMETERS:
            raise ValidationError(
                f"Invalid period '{period}'. Valid options: "
                f"{list(BACnetConstants.PERIOD_PARAMETERS.keys())}"
            )
        start_time = timezone.now() - timedelta(
            hours=BACnetConstants.PERIOD_PARAMETERS[period]
        )
        points_param = request.GET.get("points", "")
        if points_param:
            points_list = points_param.split(",")
            points = all_points.filter(identifier__in=points_list)
        else:
            points = all_points

        points_info = []

        for point in points:
            readings = point.readings.filter(read_time__gte=start_time)
            stats = readings.aggregate(
                min_value=Min(Cast("value", FloatField())),
                max_value=Max(Cast("value", FloatField())),
                avg_value=Avg(Cast("value", FloatField())),
                count=Count("id"),
            )
            points_info.append(
                {
                    "point_identifier": point.identifier,
                    "readings": [
                        {
                            "timestamp": r.read_time.isoformat(),
                            "value": float(r.value) if r.value else None,
                        }
                        for r in readings.order_by("read_time")
                    ],
                    "statistics": {
                        "min": (
                            round(stats["min_value"], 2) if stats["min_value"] else None
                        ),
                        "max": (
                            round(stats["max_value"], 2) if stats["max_value"] else None
                        ),
                        "avg": (
                            round(stats["avg_value"], 2) if stats["avg_value"] else None
                        ),
                        "count": stats["count"],
                    },
                }
            )

        return JsonResponse(
            {
                "success": True,
                "device_id": device_id,
                "period": period,
                "points": points_info,
            }
        )

    except Http404:
        raise DeviceNotFoundAPIError()


def api_docs(request):
    """
    API Documentation page
    """
    return render(request, "discovery/api_docs.html")
