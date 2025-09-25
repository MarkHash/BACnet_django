import os

import django

from discovery.models import BACnetPoint, BACnetReading
from discovery.tasks import calculate_hourly_stats, calculate_point_stats_manual

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bacnet_project.docker_settings")
django.setup()


def test_celery_tasks():
    print("🧪 Testing Celery Tasks...")

    points = BACnetPoint.objects.all()
    readings = BACnetReading.objects.all()

    print(f"📊 Found {len(points)} points and {len(readings)} readings")

    if not points:
        print("❌ No points found - run your historical data test first")
        return

    point = points[0]
    print(f"\n🎯 Testing manual task with point: {point}")

    try:
        result = calculate_point_stats_manual.delay(point.id, "hourly", 24)
        print(f"✅ Task submitted with ID: {result.id}")

        task_result = result.get(timeout=30)
        print(f"✅ Task result: {task_result}")

    except Exception as e:
        print(f"❌ Task failed: {e}")

    print("\n🕒 Testing hourly stats task...")
    try:
        result = calculate_hourly_stats.delay()
        print(f"✅ Hourly stats task submitted with ID: {result.id}")

        task_result = result.get(timeout=60)
        print(f"✅ Hourly stats result: {task_result}")

    except Exception as e:
        print(f"❌ Hourly stats task failed: {e}")


if __name__ == "__main__":
    test_celery_tasks()
