import logging
import subprocess
import sys
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .models import BACnetPoint, BACnetReading, SensorReadingStats
from .services import BACnetService

logger = logging.getLogger(__name__)


@shared_task
def calculate_hourly_stats():
    logger.info("Starting hourly stats calculation...")

    now = timezone.now().replace(minute=0, second=0, microsecond=0)
    start_time = now - timedelta(hours=1)

    points = BACnetPoint.objects.all()
    stats_created = 0

    for point in points:
        stats_created += _calculate_point_stats(point, "hourly", start_time, now)

    logger.info(f"Created {stats_created} hourly stats records")
    return {"created": stats_created, "period": "hourly", "time": str(now)}


@shared_task
def calculate_daily_stats():
    logger.info("Starting daily stats calculation...")

    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_time = today - timedelta(days=1)

    points = BACnetPoint.objects.all()
    stats_created = 0

    for point in points:
        stats_created += _calculate_point_stats(point, "daily", start_time, today)

    logger.info(f"Created {stats_created} daily stats records")
    return {"created": stats_created, "period": "daily", "time": str(today)}


def _calculate_point_stats(point, aggregation_type, start_time, end_time):
    existing_stats = SensorReadingStats.objects.filter(
        point=point, aggregation_type=aggregation_type, period_start=start_time
    ).exists()

    if existing_stats:
        logger.debug(f"Stats already exist for {point} {aggregation_type} {start_time}")
        return 0

    readings = BACnetReading.objects.filter(
        point=point, read_time__gte=start_time, read_time__lt=end_time
    )

    if not readings.exists():
        logger.debug(
            f"No readings found for {point} in period {start_time} to {end_time}"
        )
        return 0

    numeric_readings = []
    null_count = 0
    anomaly_count = 0

    for reading in readings:
        if reading.is_anomaly:
            anomaly_count += 1

        try:
            numeric_value = float(reading.value)
            numeric_readings.append(numeric_value)
        except (ValueError, TypeError):
            null_count += 1

    if not numeric_readings:
        logger.debug(f"No numeric readings found for {point}")
        return 0

    avg_value = sum(numeric_readings) / len(numeric_readings)
    min_value = min(numeric_readings)
    max_value = max(numeric_readings)
    if len(numeric_readings) > 1:
        variance = sum((x - avg_value) ** 2 for x in numeric_readings) / len(
            numeric_readings
        )
        std_dev = variance**0.5
    else:
        std_dev = 0.0

    SensorReadingStats.objects.create(
        point=point,
        aggregation_type=aggregation_type,
        period_start=start_time,
        period_end=end_time,
        avg_value=avg_value,
        min_value=min_value,
        max_value=max_value,
        std_dev=std_dev,
        reading_count=len(numeric_readings),
        null_reading_count=null_count,
        anomaly_count=anomaly_count,
    )

    logger.debug(f"Created stats for {point} {aggregation_type} {start_time}")
    return 1


@shared_task
def calculate_point_stats_manual(point_id, aggregation_type="hourly", hours_back=1):
    try:
        point = BACnetPoint.objects.get(id=point_id)
        now = timezone.now().replace(minute=0, second=0, microsecond=0)
        start_time = now - timedelta(hours=hours_back)

        result = _calculate_point_stats(point, aggregation_type, start_time, now)
        return {"point": str(point), "created": result, "period": aggregation_type}

    except BACnetPoint.DoesNotExist:
        logger.error(f"Point with id {point_id} not found")
        return {"error": "Point not found"}


@shared_task(bind=True, queue="bacnet")
def discover_devices_task(self, mock_mode=False):
    try:
        if getattr(settings, "IS_WINDOWS_HOST", False):
            cmd = [sys.executable, "manage.py", "discover_devices"]
            if mock_mode:
                cmd.append("--mock")
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60, cwd="/host_app"
            )
            if result.returncode == 0:
                return {"success": True, "output": result.stdout}
            else:
                return {"success": False, "output": result.stdout}

        else:
            service = BACnetService()
            devices = service.discover_devices(mock_mode=mock_mode)
            return {"success": True, "devices_found": len(devices) if devices else 0}
    except Exception as e:
        logger.error(f"Device discovery task failed: {e}")
        return {"error": str(e)}


@shared_task(bind=True, queue="bacnet")
def collect_readings_task(self):
    try:
        if getattr(settings, "IS_WINDOWS_HOST", False):
            cmd = [sys.executable, "manage.py", "collect_readings"]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120, cwd="/host_app"
            )
            if result.returncode == 0:
                return {"success": True, "output": result.stdout}
            else:
                return {"success": False, "output": result.stdout}

        else:
            service = BACnetService()
            results = service.collect_all_readings()
            return {
                "success": True,
                "readings_collected": results.get("readings_collected", 0),
            }
    except Exception as e:
        return {"success": False, "error": str(e)}
