import os
import random
from datetime import timedelta

import django
from django.utils import timezone

from discovery.models import BACnetDevice, BACnetPoint, BACnetReading

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bacnet_project.docker_settings")
django.setup()


def create_fresh_test_data():
    print("🧪 Creating Fresh Test Data for Statistics...")

    BACnetDevice.objects.filter(device_id__gte=8000).delete()
    print("🧹 Cleaned up old test data")

    device = BACnetDevice.objects.create(
        device_id=8001, address="192.168.1.100", vendor_id=999, is_online=True
    )
    print(f"✅ Created device: {device}")

    points = []
    for i in range(3):
        point = BACnetPoint.objects.create(
            device=device,
            object_type="analogInput",
            instance_number=i + 100,
            identifier=f"analogInput:{i+100}",
            object_name=f"Test Temperature Sensor {i+1}",
        )
        points.append(point)

    print(f"✅ Created {len(points)} test points")

    now = timezone.now()
    current_hour = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)

    print(f"📅 Creating readings for current hour: {current_hour}")

    readings_created = 0
    for point in points:
        base_temp = 20.0 + (point.instance_number % 10)

        for minute in range(0, 60, 5):
            read_time = current_hour + timedelta(minutes=minute)

            temp_variation = random.uniform(-2.0, 2.0)
            value = base_temp + temp_variation

            is_anomaly = random.random() < 0.1
            if is_anomaly:
                value += random.choice([-15, 15])

            BACnetReading.objects.create(
                point=point,
                value=str(round(value, 1)),
                read_time=read_time,
                data_quality_score=1.0,
                is_anomaly=is_anomaly,
                anomaly_score=0.9 if is_anomaly else None,
            )
            readings_created += 1

    print(f"✅ Created {readings_created} readings in current hour")

    previous_hour = current_hour - timedelta(hours=1)
    print(f"📅 Creating readings for previous hour: {previous_hour}")

    for point in points:
        base_temp = 19.0 + (point.instance_number % 10)

        for minute in range(0, 60, 10):
            read_time = previous_hour + timedelta(minutes=minute)

            temp_variation = random.uniform(-1.5, 1.5)
            value = base_temp + temp_variation

            BACnetReading.objects.create(
                point=point,
                value=str(round(value, 1)),
                read_time=read_time,
                data_quality_score=1.0,
                is_anomaly=False,
            )
            readings_created += 1
    print(f"✅ Created {readings_created} total readings")

    total_readings = BACnetReading.objects.filter(point__device=device).count()
    anomaly_count = BACnetReading.objects.filter(
        point__device=device, is_anomaly=True
    ).count()

    print("\n📊 Summary:")
    print(f"   • Device: {device}")
    print(f"   • Points: {len(points)}")
    print(f"   • Total readings: {total_readings}")
    print(f"   • Anomalies: {anomaly_count}")
    print(f"   • Time range: {previous_hour} to {now}")
    print("\n🎯 Ready to test statistics tasks!")


if __name__ == "__main__":
    create_fresh_test_data()
