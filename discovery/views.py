"""
BACnet Web API Views

This module provides REST API endpoints for BACnet device management and monitoring.
The views handle web requests for device discovery, point reading, and system status,
providing both JSON API responses and HTML dashboard interfaces.

API Endpoints:
- Device management: List, discover, and control BACnet devices
- Point operations: Read values, manage points, and trigger updates
- System status: Health checks, statistics, and operational dashboards
- Manual operations: Force discovery, clear devices, and administrative actions

Features:
- RESTful JSON responses with comprehensive error handling
- HTML dashboard views for system monitoring
- Real-time device status and connectivity information
- Integration with background task system for async operations
- Cross-platform support (Docker containers and Windows native)

The views provide the web interface layer for the BACnet monitoring system,
abstracting service layer complexity into user-friendly endpoints.
"""

import logging
from datetime import timedelta

import numpy as np
from django.db.models import Avg, Count, FloatField, Max, Min, Q
from django.db.models.functions import Cast
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .constants import BACnetConstants
from .decorators import api_error_handler, api_rate_limit
from .exceptions import (
    BACnetError,
    ConfigurationError,
    DeviceNotFoundAPIError,
    DeviceNotFoundError,
    ValidationError,
)
from .models import BACnetDevice, BACnetPoint, BACnetReading
from .serializers import (
    AnomalyReadingSerializer,
    AnomalyStatsSerializer,
    DataQualityResponseSerializer,
    DevicePerformanceResponseSerializer,
    DeviceStatusResponseSerializer,
    DeviceTrendsResponseSerializer,
)
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


class DeviceStatusAPIView(APIView):
    """
    Get status overview for all active BACnet devices
    """

    @extend_schema(
        summary="Get device status overview",
        description=(
            "Returns status information for all active BACnet devices "
            "including online/offline status and point statistics"
        ),
        responses={200: DeviceStatusResponseSerializer},
    )
    def get(self, request):
        try:
            device_info = []
            active_devices = BACnetDevice.objects.filter(is_active=True)
            for device in active_devices:
                device_status = "online"
                total_points = device.points.count()
                if device.last_seen:
                    time_since_reading = (
                        timezone.now() - device.last_seen
                    ).total_seconds()
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
            return Response(
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
                },
                status=status.HTTP_200_OK,
            )
        except Http404:
            raise DeviceNotFoundAPIError()


class DeviceTrendsAPIView(APIView):
    """
    Get historical trends for device points
    """

    def _safe_float_conversion(self, value):
        """Safely convert value to float, return None for non-numeric values"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @extend_schema(
        summary="Get device trends",
        description=(
            "Returns historical data trends for specific device points "
            "over a specified time period"
        ),
        parameters=[
            OpenApiParameter(
                "period",
                OpenApiTypes.STR,
                description=("Time period: 1hour, 6hours, 24hours, 7days, 30days"),
            ),
            OpenApiParameter(
                "points",
                OpenApiTypes.STR,
                description="Comma-separated list of point identifiers",
            ),
        ],
        responses={200: DeviceTrendsResponseSerializer},
    )
    def get(self, request, device_id):
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

                # Filter readings to only include numeric values for statistics
                numeric_readings = readings.exclude(
                    Q(value__isnull=True)
                    | Q(value__regex=r"^[^0-9\-\+\.]")
                    | Q(  # Exclude values starting with non-numeric chars
                        value__iexact="inactive"
                    )
                    | Q(value__iexact="offline")  # Explicitly exclude "inactive"
                    | Q(value__iexact="error")  # And other common text statuses
                )

                stats = numeric_readings.aggregate(
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
                                "value": self._safe_float_conversion(r.value),
                            }
                            for r in readings.order_by("read_time")
                        ],
                        "statistics": {
                            "min": (
                                round(stats["min_value"], 2)
                                if stats["min_value"]
                                else None
                            ),
                            "max": (
                                round(stats["max_value"], 2)
                                if stats["max_value"]
                                else None
                            ),
                            "avg": (
                                round(stats["avg_value"], 2)
                                if stats["avg_value"]
                                else None
                            ),
                            "count": stats["count"],
                        },
                    }
                )

            return Response(
                {
                    "success": True,
                    "device_id": device_id,
                    "period": period,
                    "points": points_info,
                },
                status=status.HTTP_200_OK,
            )

        except Http404:
            raise DeviceNotFoundAPIError()


class DevicePerformanceAPIView(APIView):
    """
    Get device performance metrics and statistics
    """

    @extend_schema(
        summary="Get device performance dashboard",
        description=(
            "Returns performance metrics for all devices including "
            "reading counts, data quality, and activity statistics"
        ),
        responses={200: DevicePerformanceResponseSerializer},
    )
    def get(self, request):
        try:
            devices_performance = []
            active_devices = BACnetDevice.objects.filter(is_active=True)

            last_24h = timezone.now() - timedelta(hours=24)

            for device in active_devices:
                all_readings = BACnetReading.objects.filter(point__device=device)
                recent_readings = all_readings.filter(read_time__gte=last_24h)

                total_readings = all_readings.count()
                readings_24h = recent_readings.count()

                quality_avg = all_readings.aggregate(
                    avg_quality=Avg("data_quality_score")
                )["avg_quality"]

                most_active = (
                    all_readings.values("point__identifier")
                    .annotate(reading_count=Count("id"))
                    .order_by("-reading_count")
                    .first()
                )
                most_active_point = (
                    most_active["point__identifier"] if most_active else None
                )

                uptime_percentage = 100.0 if device.is_online else 0.0

                devices_performance.append(
                    {
                        "device_id": device.device_id,
                        "address": device.address,
                        "total_readings": total_readings,
                        "readings_last_24h": readings_24h,
                        "avg_data_quality": quality_avg,
                        "most_active_point": most_active_point,
                        "last_reading_time": device.last_seen,
                        "uptime_percentage": uptime_percentage,
                    }
                )

                total_devices = len(devices_performance)
                online_devices = len(
                    [d for d in devices_performance if d["uptime_percentage"] > 0]
                )
                total_readings_all = sum(
                    d["total_readings"] for d in devices_performance
                )

            return Response(
                {
                    "success": True,
                    "summary": {
                        "total_devices": total_devices,
                        "online_devices": online_devices,
                        "total_readings": total_readings_all,
                        "avg_readings_per_device": (
                            round(total_readings_all / total_devices, 2)
                            if total_devices > 0
                            else 0
                        ),
                    },
                    "devices": devices_performance,
                    "timestamp": timezone.now(),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


def calculate_completeness_score(point, expected_reading_per_point):
    actual_readings = BACnetReading.objects.filter(
        point=point, read_time__gte=timezone.now() - timedelta(hours=24)
    ).count()
    completeness_score = min((actual_readings / expected_reading_per_point) * 100, 100)
    return actual_readings, completeness_score


def calculate_accuracy_score(point):
    outliers = []
    readings_values = BACnetReading.objects.filter(
        point=point, read_time__gte=timezone.now() - timedelta(hours=24)
    ).values_list("value", flat=True)

    # Filter out non-numeric values
    numeric_values = []
    for value in readings_values:
        try:
            numeric_values.append(float(value))
        except (ValueError, TypeError):
            continue

    if len(numeric_values) > 4:
        q1 = np.percentile(numeric_values, 25)
        q3 = np.percentile(numeric_values, 75)
        iqr = q3 - q1
        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)

        outliers = [v for v in numeric_values if v < lower_bound or v > upper_bound]
        accuracy_score = max(0, (1 - len(outliers) / len(numeric_values)) * 100)
    else:
        accuracy_score = 100

    return outliers, accuracy_score


def calculate_freshness_score(point):
    latest_reading = (
        BACnetReading.objects.filter(point=point).order_by("-read_time").first()
    )
    if latest_reading:
        hours_since_last = (
            timezone.now() - latest_reading.read_time
        ).total_seconds() / 3600
        freshness_score = max(0, 100 * (0.9**hours_since_last))
    else:
        freshness_score = 0
    return latest_reading, freshness_score


def calculate_consistency_score(point):
    readings = BACnetReading.objects.filter(
        point=point, read_time__gte=timezone.now() - timedelta(hours=24)
    ).order_by("read_time")

    if len(readings) > 2:
        intervals = []
        for i in range(1, len(readings)):
            interval = (
                readings[i].read_time - readings[i - 1].read_time
            ).total_seconds() / 60
            intervals.append(interval)

        std_dev = np.std(intervals)
        consistency_score = max(0, 100 - (std_dev * 2))
    else:
        consistency_score = 50

    return consistency_score


class DataQualityAPIView(APIView):
    @extend_schema(
        summary="Get data quality metrics for all devices",
        description="Analyze data completeness, accuracy, freshness, and consistency "
        "across all devices",
        responses={200: DataQualityResponseSerializer},
    )
    def get(self, request):
        EXPECTED_INTERVAL_MINUTES = 5
        time_period_hours = 24
        try:
            devices_quality = []
            active_devices = BACnetDevice.objects.filter(is_active=True)
            total_readings = BACnetReading.objects.count()

            for device in active_devices:
                device_readings = BACnetReading.objects.filter(point__device=device)
                device_points = BACnetPoint.objects.filter(device=device)

                expected_reading_per_point = (
                    time_period_hours * 60
                ) / EXPECTED_INTERVAL_MINUTES
                point_completeness_scores = []
                point_accuracy_scores = []
                point_freshness_scores = []
                point_consistency_scores = []
                point_overall_scores = []
                point_quality_data = []
                points_with_recent_data = 0
                all_intervals = []
                for point in device_points:
                    actual_readings, completeness_score = calculate_completeness_score(
                        point, expected_reading_per_point
                    )
                    point_completeness_scores.append(completeness_score)
                    if actual_readings > 0:
                        points_with_recent_data += 1
                    outliers, accuracy_score = calculate_accuracy_score(point)
                    point_accuracy_scores.append(accuracy_score)
                    latest_reading, freshness_score = calculate_freshness_score(point)
                    point_freshness_scores.append(freshness_score)
                    consistency_score = calculate_consistency_score(point)
                    point_consistency_scores.append(consistency_score)

                    readings = BACnetReading.objects.filter(
                        point=point, read_time__gte=timezone.now() - timedelta(hours=24)
                    ).order_by("read_time")

                    if len(readings) > 1:
                        for i in range(1, len(readings)):
                            interval_minutes = (
                                readings[i].read_time - readings[i - 1].read_time
                            ).total_seconds() / 60
                            all_intervals.append(interval_minutes)

                    overall_score = (
                        completeness_score * 0.4
                        + accuracy_score * 0.3
                        + freshness_score * 0.2
                        + consistency_score * 0.1
                    )
                    point_overall_scores.append(overall_score)
                    point_quality_data.append(
                        {
                            "point_identifier": (
                                f"{point.object_type}:{point.instance_number}"
                            ),
                            "total_readings": actual_readings,
                            "missing_readings": max(
                                0, expected_reading_per_point - actual_readings
                            ),
                            "outlier_count": (
                                len(outliers) if "outliers" in locals() else 0
                            ),
                            "last_reading_time": (
                                latest_reading.read_time if latest_reading else None
                            ),
                            "data_gaps_hours": 0,
                            "quality_score": overall_score,
                        }
                    )

                total_device_points = len(device_points)
                coverage = (
                    (points_with_recent_data / total_device_points * 100)
                    if total_device_points > 0
                    else 0
                )
                avg_interval = (
                    sum(all_intervals) / len(all_intervals) if all_intervals else None
                )

                devices_quality.append(
                    {
                        "device_id": device.id,
                        "address": device.address,
                        "metrics": {
                            "completeness_score": (
                                sum(point_completeness_scores)
                                / len(point_completeness_scores)
                                if point_completeness_scores
                                else 0
                            ),
                            "accuracy_score": (
                                sum(point_accuracy_scores) / len(point_accuracy_scores)
                                if point_accuracy_scores
                                else 0
                            ),
                            "freshness_score": (
                                sum(point_freshness_scores)
                                / len(point_freshness_scores)
                                if point_freshness_scores
                                else 0
                            ),
                            "consistency_score": (
                                sum(point_consistency_scores)
                                / len(point_consistency_scores)
                                if point_consistency_scores
                                else 0
                            ),
                            "overall_quality_score": (
                                sum(point_overall_scores) / len(point_overall_scores)
                                if point_overall_scores
                                else 0
                            ),
                        },
                        "point_quality": point_quality_data,
                        "data_coverage_percentage": coverage,
                        "avg_reading_interval_minutes": avg_interval,
                    }
                )

            if devices_quality:
                num_devices = len(devices_quality)
                summary_completeness = (
                    sum(d["metrics"]["completeness_score"] for d in devices_quality)
                    / num_devices
                )
                summary_accuracy_score = (
                    sum(d["metrics"]["accuracy_score"] for d in devices_quality)
                    / num_devices
                )
                summary_freshness_score = (
                    sum(d["metrics"]["freshness_score"] for d in devices_quality)
                    / num_devices
                )
                summary_consistency_score = (
                    sum(d["metrics"]["consistency_score"] for d in devices_quality)
                    / num_devices
                )
                summary_overall_quality_score = (
                    sum(d["metrics"]["overall_quality_score"] for d in devices_quality)
                    / num_devices
                )
            else:
                summary_completeness = summary_accuracy_score = (
                    summary_freshness_score
                ) = summary_consistency_score = summary_overall_quality_score = 0

            return Response(
                {
                    "success": True,
                    "summary": {
                        "completeness_score": summary_completeness,
                        "accuracy_score": summary_accuracy_score,
                        "freshness_score": summary_freshness_score,
                        "consistency_score": summary_consistency_score,
                        "overall_score": summary_overall_quality_score,
                    },
                    "devices": devices_quality,
                    "timestamp": timezone.now(),
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AnomalyListAPIView(APIView):
    @extend_schema(
        summary="List recent anomalies with filtering",
        description="Retrieve anomaly readings with optional filtering by time range, "
        "device, and anomaly status. Supports pagination and includes device context.",
        parameters=[
            OpenApiParameter(
                "hours", int, description="Time range in hours (default: 24)"
            ),
            OpenApiParameter(
                "device_id", int, description="Filter by specific device ID"
            ),
            OpenApiParameter(
                "anomalies_only", bool, description="Show only anomalous readings"
            ),
            OpenApiParameter(
                "limit", int, description="Maximum number of results (default: 100)"
            ),
        ],
        responses={200: AnomalyReadingSerializer(many=True)},
    )
    def get(self, request):
        try:
            hours = int(request.GET.get("hours", 24))
            device_id = request.GET.get("device_id")
            anomalies_only = (
                request.GET.get("anomalies_only", "false").lower() == "true"
            )
            limit = int(request.GET.get("limit", 100))

            time_threshold = timezone.now() - timedelta(hours=hours)
            queryset = (
                BACnetReading.objects.filter(read_time__gte=time_threshold)
                .select_related("point__device")
                .order_by("-read_time")
            )

            if device_id:
                queryset = queryset.filter(point__device__device_id=device_id)
            if anomalies_only:
                queryset = queryset.filter(is_anomaly=True)

            readings = queryset[:limit]
            serializer = AnomalyReadingSerializer(readings, many=True)

            return Response(
                {
                    "success": True,
                    "count": len(readings),
                    "filters": {
                        "hours": hours,
                        "device_id": device_id,
                        "anomalies_only": anomalies_only,
                        "limit": limit,
                    },
                    "data": serializer.data,
                    "timestamp": timezone.now(),
                }
            )

        except Exception as e:
            return Response(
                {"success": False, "error": str(e), "timestamp": timezone.now()},
                status=500,
            )


class DeviceAnomalyAPIView(APIView):
    @extend_schema(
        summary="Get anomalies for specific device",
        description="Retrieve anomaly readings and statistics for a specific device",
        parameters=[
            OpenApiParameter(
                "hours", int, description="Time range in hours (default: 24)"
            ),
            OpenApiParameter(
                "anomalies_only", bool, description="Show only anomalous readings"
            ),
            OpenApiParameter(
                "limit", int, description="Maximum number of results (default: 100)"
            ),
        ],
        responses={200: AnomalyReadingSerializer(many=True)},
    )
    def get(self, request, device_id):
        try:
            hours = int(request.GET.get("hours", 24))
            anomalies_only = (
                request.GET.get("anomalies_only", "false").lower() == "true"
            )
            limit = int(request.GET.get("limit", 100))

            time_threshold = timezone.now() - timedelta(hours=hours)
            queryset = (
                BACnetReading.objects.filter(
                    read_time__gte=time_threshold, point__device__device_id=device_id
                )
                .select_related("point__device")
                .order_by("-read_time")
            )

            if anomalies_only:
                queryset = queryset.filter(is_anomaly=True)

            readings = queryset[:limit]
            serializer = AnomalyReadingSerializer(readings, many=True)

            return Response(
                {
                    "success": True,
                    "count": len(readings),
                    "filters": {
                        "hours": hours,
                        "device_id": device_id,
                        "anomalies_only": anomalies_only,
                        "limit": limit,
                    },
                    "data": serializer.data,
                    "timestamp": timezone.now(),
                }
            )

        except Exception as e:
            return Response(
                {"success": False, "error": str(e), "timestamp": timezone.now()},
                status=500,
            )


class AnomalyStatsAPIView(APIView):
    @extend_schema(
        summary="Get system-wide anomaly statistics",
        description=(
            "Retrieve comprehensive anomaly statistics including counts, "
            "rates, and top affected devices"
        ),
        parameters=[
            OpenApiParameter(
                "days",
                int,
                description="Time range in days for statistics (default: 7)",
            ),
        ],
        responses={200: AnomalyStatsSerializer},
    )
    def get(self, request):
        try:
            days = int(request.GET.get("days", 7))

            time_threshold = timezone.now() - timedelta(days=days)
            today_threshold = timezone.now() - timedelta(days=1)

            total_anomalies = BACnetReading.objects.filter(
                read_time__gte=time_threshold, is_anomaly=True
            ).count()

            anomalies_today = BACnetReading.objects.filter(
                read_time__gte=today_threshold, is_anomaly=True
            ).count()

            total_readings = BACnetReading.objects.filter(
                read_time__gte=time_threshold
            ).count()

            anomaly_rate = (
                (total_anomalies / total_readings * 100) if total_readings > 0 else 0
            )

            top_anomaly_devices = (
                BACnetReading.objects.filter(
                    read_time__gte=time_threshold, is_anomaly=True
                )
                .values("point__device__device_id", "point__device__address")
                .annotate(anomaly_count=Count("id"))
                .order_by("-anomaly_count")[:5]
            )

            return Response(
                {
                    "success": True,
                    "period_days": days,
                    "data": {
                        "total_anomalies": total_anomalies,
                        "anomalies_today": anomalies_today,
                        "top_anomalies_devices": list(top_anomaly_devices),
                        "anomaly_rate": round(anomaly_rate, 2),
                    },
                    "timestamp": timezone.now(),
                }
            )

        except Exception as e:
            return Response(
                {"success": False, "error": str(e), "timestamp": timezone.now()},
                status=500,
            )
