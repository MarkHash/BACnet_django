import os
from datetime import timedelta

import django
from django.utils import timezone

from discovery.models import BACnetPoint, BACnetReading, SensorReadingStats

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bacnet_project.docker_settings")
django.setup()


def debug_task_logic():
    print("🔍 Debugging Task Logic...")

    # Get the same point the task is using
    point = BACnetPoint.objects.first()
    if not point:
        print("❌ No points found in database!")
        return

    print(f"🎯 Testing point: {point}")
    print(f"   • Device: {point.device}")
    print(f"   • Point ID: {point.id}")

    # Check what readings exist for this point
    readings = BACnetReading.objects.filter(point=point)
    print(f"\n📊 Total readings for this point: {readings.count()}")

    if readings.exists():
        print("📋 Sample readings:")
        for reading in readings[:5]:
            print(f"   • Value: {reading.value}, Time: {reading.read_time}")

        # Show time range of all readings
        earliest = readings.order_by("read_time").first().read_time
        latest = readings.order_by("read_time").last().read_time
        print(f"📅 Reading time range: {earliest} to {latest}")
    else:
        print("❌ No readings found for this point!")
        return

    # Check the task's time window (24 hours back from now)
    now = timezone.now().replace(minute=0, second=0, microsecond=0)
    start_time = now - timedelta(hours=24)
    print(f"\n🕐 Task time window: {start_time} to {now}")

    readings_in_window = BACnetReading.objects.filter(
        point=point, read_time__gte=start_time, read_time__lt=now
    )
    print(f"📊 Readings in time window: {readings_in_window.count()}")

    if readings_in_window.exists():
        print("📋 Readings in time window:")
        for reading in readings_in_window[:5]:
            print(f"   • Value: {reading.value}, Time: {reading.read_time}")

    # Check if stats already exist
    existing_stats = SensorReadingStats.objects.filter(point=point)
    print(f"\n📈 Existing stats for this point: {existing_stats.count()}")

    if existing_stats.exists():
        print("📋 Existing statistics:")
        for stat in existing_stats:
            print(
                f"   • {stat.aggregation_type} for {stat.period_start} - "
                f"{stat.period_end}"
            )
            print(f"     Avg: {stat.avg_value}, Count: {stat.reading_count}")
    else:
        print("✅ No existing stats - ready to create new ones")

    # Check numeric readings (what the task actually processes)
    numeric_readings = []
    for reading in readings_in_window:
        try:
            numeric_value = float(reading.value)
            numeric_readings.append(numeric_value)
        except (ValueError, TypeError):
            pass

    print(f"\n🔢 Numeric readings in window: {len(numeric_readings)}")
    if numeric_readings:
        print(f"   • Values: {numeric_readings[:10]}...")  # Show first 10


if __name__ == "__main__":
    debug_task_logic()
