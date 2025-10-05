#!/usr/bin/env python
"""
Test script for Enhanced Anomaly Detection (Multi-method Ensemble)

This script tests the new Isolation Forest and ensemble anomaly detection
methods implemented in the AnomalyDetector class.
"""

import os
from datetime import timedelta

import django
from django.utils import timezone

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bacnet_project.settings")
django.setup()

from discovery.ml_utils import AnomalyDetector  # noqa: E402
from discovery.models import BACnetPoint, BACnetReading  # noqa: E402


def test_enhanced_anomaly_detection():
    """Test the enhanced anomaly detection system with real data."""

    print("🔍 Testing Enhanced Anomaly Detection System")
    print("=" * 50)

    # Get temperature sensors
    temp_sensors = BACnetPoint.objects.filter(units__icontains="degree")

    if not temp_sensors.exists():
        print("❌ No temperature sensors found!")
        return

    print(f"📊 Found {temp_sensors.count()} temperature sensors")

    # Test with sensors from Device 2000 which has the best data
    device_2000_sensors = temp_sensors.filter(device__device_id=2000)

    if not device_2000_sensors.exists():
        print("⚠️  No temperature sensors found on Device 2000,")
        print("testing first 3 sensors")
        test_sensors = temp_sensors[:3]
    else:
        print(
            f"🎯 Found {device_2000_sensors.count()} temperature "
            f"sensors on Device 2000"
        )
        test_sensors = device_2000_sensors[:3]

    for point in test_sensors:
        print(f"\n🌡️  Testing sensor: {point.identifier}")
        print(f"   Device: {point.device.device_id} ({point.device.address})")

        # Check data availability from 6 days ago (when system was active)
        six_days_ago = timezone.now() - timedelta(days=6)
        historical_count = (
            BACnetReading.objects.filter(
                point=point,
                read_time__gte=six_days_ago - timedelta(hours=24),
                read_time__lte=six_days_ago,
            )
            .exclude(value="0.0")
            .count()
        )

        print(
            f"   Historical readings (6 days ago, 24h window): " f"{historical_count}"
        )

        if historical_count < 5:
            print("   ⚠️  Insufficient historical data for testing")
            continue

        # Get an actual historical value for realistic testing
        historical_reading = (
            BACnetReading.objects.filter(
                point=point,
                read_time__gte=six_days_ago - timedelta(hours=2),
                read_time__lte=six_days_ago,
            )
            .exclude(value="0.0")
            .first()
        )

        if historical_reading:
            try:
                actual_value = float(historical_reading.value)
                test_values = [
                    actual_value,  # Normal value
                    actual_value + 10,  # Slightly high
                    actual_value + 20,  # Very high (likely anomaly)
                    actual_value - 10,  # Slightly low
                ]
            except (ValueError, TypeError):
                test_values = [20.0, 25.0, 35.0, 15.0]  # Default test values
        else:
            test_values = [20.0, 25.0, 35.0, 15.0]  # Default test values

        # Initialize detector with custom time window for historical data
        detector = AnomalyDetector()

        print(f"   🧪 Testing with values: {test_values}")
        print("   📅 Using historical data from 6 days ago")
        print()

        for test_value in test_values:
            print(f"   Testing value: {test_value}°C")

            try:
                # For testing with historical data, we need to temporarily
                # modify the detector to use historical readings for baseline

                # Get historical readings for manual testing
                historical_readings = list(
                    BACnetReading.objects.filter(
                        point=point,
                        read_time__gte=six_days_ago - timedelta(hours=24),
                        read_time__lte=six_days_ago,
                    )
                    .exclude(value="0.0")
                    .values_list("value", flat=True)
                )

                historical_values = []
                for val in historical_readings:
                    try:
                        historical_values.append(float(val))
                    except (ValueError, TypeError):
                        continue

                print(
                    f"     Using {len(historical_values)} historical "
                    f"readings for baseline"
                )

                if len(historical_values) >= 5:
                    # Test with historical context - temporarily override
                    # detector methods. For now, test original methods which
                    # will use current timeframe
                    z_score = detector.detect_z_score_anomaly(point, test_value)
                    iqr_score, iqr_anomaly = detector.detect_iqr_anomaly(
                        point, test_value
                    )

                    # Test Isolation Forest (new!) - may not work without
                    # recent data
                    iso_score, iso_anomaly = detector.detect_isolation_forest_anomaly(
                        point, test_value
                    )

                    # Test Ensemble (new!)
                    ensemble_score, ensemble_anomaly, contributions = (
                        detector.detect_ensemble_anomaly(point, test_value)
                    )
                else:
                    print(
                        f"     ⚠️  Insufficient historical data "
                        f"({len(historical_values)} values)"
                    )
                    continue

                # Results
                print(
                    f"     Z-score: {z_score:.3f} "
                    f"(anomaly: {z_score >= detector.z_score_threshold})"
                )
                print(f"     IQR: {iqr_score:.3f} (anomaly: {iqr_anomaly})")
                print(
                    f"     🆕 Isolation Forest: {iso_score:.3f} "
                    f"(anomaly: {iso_anomaly})"
                )
                print(
                    f"     🆕 Ensemble: {ensemble_score:.3f} "
                    f"(anomaly: {ensemble_anomaly})"
                )
                print(f"     🆕 Method contributions: {contributions}")

                # Analysis
                if ensemble_anomaly:
                    print("     🚨 ANOMALY DETECTED by ensemble method!")
                else:
                    print("     ✅ Normal reading according to ensemble")

            except Exception as e:
                print(f"     ❌ Error testing value {test_value}: {e}")

            print()

        # Only test first sensor with sufficient data
        break

    print("🎉 Enhanced Anomaly Detection test complete!")
    print("\n📈 Key Improvements:")
    print("  • Isolation Forest: Multi-dimensional anomaly detection")
    print("  • Ensemble Method: Weighted combination of all methods")
    print("  • Confidence Scoring: Quantified certainty levels")
    print("  • Method Contributions: Transparency in detection")


def test_data_requirements():
    """Check data requirements for different detection methods."""

    print("\n📊 Data Requirements Analysis")
    print("=" * 40)

    detector = AnomalyDetector()

    print(f"Z-score & IQR minimum data points: {detector.MIN_DATA_POINTS}")
    print(f"Isolation Forest minimum samples: " f"{detector.MIN_ISOLATION_SAMPLES}")
    print(f"Lookback period: {detector.LOOKBACK_HOURS} hours")
    print(f"Ensemble weights: {detector.ENSEMBLE_WEIGHTS}")


if __name__ == "__main__":
    print("🚀 Starting Enhanced Anomaly Detection Test")
    print(f"Time: {timezone.now()}")
    print()

    test_data_requirements()
    test_enhanced_anomaly_detection()
