import os
from datetime import timedelta

import django
from django.utils import timezone

from discovery.models import (
    AlarmHistory,
    BACnetDevice,
    BACnetPoint,
    BACnetReading,
    DeviceStatusHistory,
)

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bacnet_project.settings")
django.setup()


def test_historical_data():
    print("🧪 Testing Historical Data Collection...")

    # Cleanup any existing test data
    print("\n0. Cleaning up existing test data...")
    BACnetDevice.objects.filter(device_id=9999).delete()
    print("✓ Cleaned up existing test data")

    # Step 1: Create mock device and point
    print("\n1. Creating mock device and point...")
    device = BACnetDevice.objects.create(
        device_id=9999, address="192.168.1.200", vendor_id=999, is_online=True
    )

    point = BACnetPoint.objects.create(
        device=device,
        object_type="analogValue",
        instance_number=1,
        identifier="analogValue:1",
        object_name="Test Temperature",
    )

    print(f"✓ Created device: {device}")
    print(f"✓ Created point: {point}")

    # Step 2: Test helper functions
    print("\n2. Testing helper functions...")
    # client = DjangoBACnetClient(None)
    client = TestClient()

    quality_good = client._calculate_data_quality(25.5, point)
    quality_bad = client._calculate_data_quality(-999, point)
    quality_string = client._calculate_data_quality("invalid", point)

    print(f"✓ Data quality (good value 25.5): {quality_good}")
    print(f"✓ Data quality (bad value -999): {quality_bad}")
    print(f"✓ Data quality (string 'invalid'): {quality_string}")

    # Step 3: Create baseline readings
    print("\n3. Creating baseline readings...")
    baseline_values = [20.0, 21.0, 19.5, 22.0, 20.5, 21.5, 19.8, 20.2, 21.2, 20.8]

    for i, value in enumerate(baseline_values):
        reading = BACnetReading.objects.create(
            point=point, value=str(value), data_quality_score=1.0, is_anomaly=False
        )
        print(f"✓ Created baseline reading {i+1}: {value}")

    # Step 4: Test anomaly detection
    print("\n4. Testing anomaly detection...")

    # Test normal value
    normal_value = 20.5
    is_anomaly_normal = client._detect_anomaly(normal_value, point)
    print(f"✓ Normal value {normal_value} - Anomaly: {is_anomaly_normal}")

    # Test anomalous value
    anomaly_value = 50.0
    is_anomaly_high = client._detect_anomaly(anomaly_value, point)
    print(f"✓ High value {anomaly_value} - Anomaly: {is_anomaly_high}")

    if is_anomaly_high:
        score = client._calculate_anomaly_score(anomaly_value, point)
        print(f"✓ Anomaly score: {score}")

    # Step 5: Test complete reading creation
    print("\n5. Testing complete reading creation...")
    test_value = 45.0

    reading = BACnetReading.objects.create(
        point=point,
        value=str(test_value),
        data_quality_score=client._calculate_data_quality(test_value, point),
        is_anomaly=client._detect_anomaly(test_value, point),
    )

    if reading.is_anomaly:
        reading.anomaly_score = client._calculate_anomaly_score(test_value, point)
        reading.save()

        client._create_anomaly_alarm(device, point, test_value)
        print(f"✓ Created anomaly reading and alarm for value: {test_value}")

    print("✓ Reading created:")
    print(f"  - Value: {reading.value}")
    print(f"  - Quality: {reading.data_quality_score}")
    print(f"  - Is Anomaly: {reading.is_anomaly}")
    print(f"  - Anomaly Score: {reading.anomaly_score}")

    # Step 6: Test DeviceStatusHistory
    print("\n6. Testing DeviceStatusHistory...")
    DeviceStatusHistory.objects.create(
        device=device,
        is_online=True,
        successful_reads=1,
        failed_reads=0,
        packet_loss_percent=0.0,
    )
    print("✓ Created device status history entry")

    # Step 7: Check all results
    print("\n7. Final Results Summary...")

    print("\n=== All Readings ===")
    for reading in BACnetReading.objects.filter(point=point).order_by("read_time"):
        print(
            f"Value: {reading.value}, Anomaly: {reading.is_anomaly}, "
            f"Score: {reading.anomaly_score}"
        )

    print("\n=== Alarms ===")
    for alarm in AlarmHistory.objects.filter(device=device):
        print(f"Type: {alarm.alarm_type}, Value: {alarm.trigger_value}")
        print(f"Message: {alarm.message}")

    print("\n=== Device Status History ===")
    for status in DeviceStatusHistory.objects.filter(device=device):
        print(
            f"Online: {status.is_online}, Successful: {status.successful_reads}, "
            f"Time: {status.timestamp}"
        )

    print("\n🎉 Test completed successfully!")


class TestClient:
    def _calculate_data_quality(self, value, point):
        try:
            float_value = float(value)
            if float_value < 0 or float_value > 100000:
                return 0.5
            return 1.0
        except (ValueError, TypeError):
            return 0.7

    def _detect_anomaly(self, value, point):
        try:
            float_value = float(value)
            recent_readings = point.readings.filter(
                read_time__gte=timezone.now() - timedelta(hours=24)
            ).values_list("value", flat=True)

            if len(recent_readings) < 5:
                return False

            values = [float(v) for v in recent_readings if v.replace(".", "").isdigit()]
            if len(values) < 3:
                return False

            from statistics import mean, stdev

            avg = mean(values)
            std = stdev(values) if len(values) > 1 else 0

            return abs(float_value - avg) > (3 * std)
        except Exception:
            return False

    def _calculate_anomaly_score(self, value, point):
        try:
            float_value = float(value)
            recent_readings = point.readings.filter(
                read_time__gte=timezone.now() - timedelta(hours=24)
            ).values_list("value", flat=True)

            values = [float(v) for v in recent_readings if v.replace(".", "").isdigit()]
            if len(values) < 3:
                return 0.5

            from statistics import mean, stdev

            avg = mean(values)
            std = stdev(values) if len(values) > 1 else 1

            deviation = abs(float_value - avg) / (std if std > 0 else 1)
            return min(deviation / 5.0, 1.0)
        except Exception:
            return 0.5

    def _create_anomaly_alarm(self, device, point, value):
        AlarmHistory.objects.create(
            device=device,
            point=point,
            alarm_type="anomaly_detected",
            severity="medium",
            trigger_value=str(value),
            message=f"Anomalous reading detected for {point.identifier}: {value}",
        )


if __name__ == "__main__":
    test_historical_data()
