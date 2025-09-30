#!/usr/bin/env python
"""
Test script for anomaly detection system
Run with: python test_anomaly_detection.py
"""

import os
import random
import sys
from datetime import timedelta

import django
from django.utils import timezone

from discovery.models import BACnetPoint, BACnetReading
from discovery.services import BACnetService

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bacnet_project.settings")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()


def test_anomaly_detection():
    test_point_id = 4047
    base_temp = 28.0
    service = BACnetService()

    print("=" * 60)
    print("BACnet Anomaly Detection Test")
    print("=" * 60)

    try:
        point = BACnetPoint.objects.get(id=test_point_id)
        if "degree" not in point.units.lower():
            print(
                f"  ⚠️  Warning: Point {point.identifier} has units "
                f"'{point.units}' - may not be temperature"
            )
    except BACnetPoint.DoesNotExist:
        print(f"   ❌ ERROR: Point ID {test_point_id} not found")
        return

    print(f"\n1. Using sensor: {point.identifier} ({point.units})")
    print(f"   Device ID: {point.device_id}")

    print("\n2. Creating test readings with variation...")

    temp_values = []
    for i in range(20):
        temp = round(base_temp + random.uniform(-3, 3), 1)
        temp_values.append(temp)

        try:
            reading = BACnetReading.objects.create(
                point=point,
                value=str(temp),
                anomaly_score=0.0,
                is_anomaly=False,
                read_time=timezone.now() - timedelta(minutes=i),
            )
        except Exception as e:
            print(f"   ⚠️  Database warning: {e}")
            continue

    print("   Created 20 test readings")
    print(f"   Range: {min(temp_values):.1f}°C to {max(temp_values):.1f}°C")
    print(f"   Average: {sum(temp_values)/len(temp_values):.1f}°C")
    std_dev_estimate = (max(temp_values) - min(temp_values)) / 4
    print(f"   Standard deviation estimate: ~{std_dev_estimate:.1f}°C")

    print("\n3. Testing anomaly detection...")

    print("\n4. Test Results:")
    print("-" * 50)

    test_cases = [
        ("Normal reading", 29.0),
        ("Slightly high", 32.0),
        ("High anomaly", 45.0),
        ("Extreme high", 80.0),
        ("Low anomaly", 5.0),
        ("Extreme low", -10.0),
    ]

    for description, test_temp in test_cases:
        z_score, iqr_score, combined_anomaly = service._detect_anomaly_if_temperature(
            point, str(test_temp)
        )
        status = "✅ Normal" if not combined_anomaly else "🚨 ANOMALY"
        # Individual method results
        z_score > 2.5 if z_score else False

        print(
            f"   {description:15} | {test_temp:6.1f}°C | "
            f"Z-score: {z_score:6.2f} | IQR: {iqr_score:6.2f} | {status}"
        )

    print("\n5. Database Verification:")
    print("-" * 50)
    recent_anomalies = BACnetReading.objects.filter(
        point=point,
        is_anomaly=True,
        read_time__gte=timezone.now() - timedelta(minutes=10),
    ).order_by("-read_time")[:5]

    if recent_anomalies.exists():
        print("  Recent anomalies stored in database:")
        for reading in recent_anomalies:
            print(
                f"  {reading.read_time.strftime('%H:%M:%S')} | "
                f"{reading.value} °C | Z-score: {reading.anomaly_score:.2f}"
            )
    else:
        print("  Note: Test readings not stored in database (detection only)")
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_anomaly_detection()
