"""
BACnet API Views Module - Simplified Core Version

This module contains core API views that provide JSON endpoints for the
BACnet device discovery and monitoring system.

API Views:
- DeviceStatusAPIView: Real-time device status and connectivity monitoring
- DeviceTrendsAPIView: Historical data trends for device points

All views return structured JSON responses with comprehensive error handling,
DRF spectacular documentation, and proper HTTP status codes.
"""

from datetime import timedelta
from typing import Any, Optional

from django.db.models import Avg, Count, FloatField, Max, Min, Q
from django.db.models.functions import Cast
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .constants import BACnetConstants
from .exceptions import (
    DeviceNotFoundAPIError,
    ValidationError,
)
from .models import (
    BACnetDevice,
)
from .serializers import (
    DeviceStatusResponseSerializer,
    DeviceTrendsResponseSerializer,
)


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

    def _safe_float_conversion(self, value: Any) -> Optional[float]:
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
