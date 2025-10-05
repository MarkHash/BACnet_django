"""
Django management command to create test ensemble anomaly data
for testing the enhanced anomaly dashboard display with method contributions
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from discovery.models import AlarmHistory, BACnetDevice, BACnetPoint


class Command(BaseCommand):
    help = (
        "Create test ensemble anomaly data with method contributions "
        "for dashboard testing"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--count", type=int, default=10, help="Number of test anomalies to create"
        )

    def handle(self, *args, **options):
        count = options["count"]

        # Get available devices and points
        devices = list(BACnetDevice.objects.all()[:3])  # Use first 3 devices
        if not devices:
            self.stdout.write(
                self.style.ERROR("No BACnet devices found. Run discovery first.")
            )
            return

        points = list(BACnetPoint.objects.filter(device__in=devices)[:5])
        if not points:
            self.stdout.write(
                self.style.ERROR("No BACnet points found. Run point discovery first.")
            )
            return

        # Enhanced ensemble anomaly scenarios
        anomaly_scenarios = [
            {
                "alarm_type": "anomaly_detected",
                "severity": "high",
                "trigger_value": "35.7",
                "threshold_value": "0.85",
                "message": (
                    "Ensemble anomaly detected: analogInput:1202006 = 35.7°C "
                    "(Ensemble: 0.85) Methods: z_score: 0.92, iqr: 0.76, "
                    "isolation_forest: 0.88, ensemble: 0.85"
                ),
            },
            {
                "alarm_type": "anomaly_detected",
                "severity": "medium",
                "trigger_value": "16.2",
                "threshold_value": "0.63",
                "message": (
                    "Ensemble anomaly detected: analogInput:1204006 = 16.2°C "
                    "(Ensemble: 0.63) Methods: z_score: 0.78, iqr: 0.65, "
                    "isolation_forest: 0.45, ensemble: 0.63"
                ),
            },
            {
                "alarm_type": "anomaly_detected",
                "severity": "high",
                "trigger_value": "42.1",
                "threshold_value": "0.94",
                "message": (
                    "Ensemble anomaly detected: analogInput:1203006 = 42.1°C "
                    "(Ensemble: 0.94) Methods: z_score: 0.98, iqr: 0.89, "
                    "isolation_forest: 0.95, ensemble: 0.94"
                ),
            },
            {
                "alarm_type": "anomaly_detected",
                "severity": "medium",
                "trigger_value": "27.8",
                "threshold_value": "0.68",
                "message": (
                    "Ensemble anomaly detected: analogValue:1201006 = 27.8°C "
                    "(Ensemble: 0.68) Methods: z_score: 0.54, iqr: 0.71, "
                    "isolation_forest: 0.79, ensemble: 0.68"
                ),
            },
            {
                "alarm_type": "anomaly_detected",
                "severity": "high",
                "trigger_value": "13.4",
                "threshold_value": "0.81",
                "message": (
                    "Ensemble anomaly detected: analogInput:1202006 = 13.4°C "
                    "(Ensemble: 0.81) Methods: z_score: 0.87, iqr: 0.83, "
                    "isolation_forest: 0.72, ensemble: 0.81"
                ),
            },
            {
                "alarm_type": "anomaly_detected",
                "severity": "medium",
                "trigger_value": "26.5",
                "threshold_value": "0.59",
                "message": (
                    "Ensemble anomaly detected: analogInput:1204006 = 26.5°C "
                    "(Ensemble: 0.59) Methods: z_score: 0.45, iqr: 0.61, "
                    "isolation_forest: 0.71, ensemble: 0.59"
                ),
            },
            {
                "alarm_type": "anomaly_detected",
                "severity": "high",
                "trigger_value": "38.9",
                "threshold_value": "0.89",
                "message": (
                    "Ensemble anomaly detected: analogInput:1203006 = 38.9°C "
                    "(Ensemble: 0.89) Methods: z_score: 0.91, iqr: 0.86, "
                    "isolation_forest: 0.90, ensemble: 0.89"
                ),
            },
            {
                "alarm_type": "anomaly_detected",
                "severity": "medium",
                "trigger_value": "15.8",
                "threshold_value": "0.65",
                "message": (
                    "Ensemble anomaly detected: analogValue:1201006 = 15.8°C "
                    "(Ensemble: 0.65) Methods: z_score: 0.72, iqr: 0.58, "
                    "isolation_forest: 0.65, ensemble: 0.65"
                ),
            },
        ]

        created_count = 0

        for i in range(count):
            # Cycle through scenarios and devices/points
            scenario = anomaly_scenarios[i % len(anomaly_scenarios)]
            device = devices[i % len(devices)]
            point = points[i % len(points)]

            # Create anomaly with recent timestamp (last 24 hours)
            hours_ago = (i % 24) + 1  # 1-24 hours ago
            triggered_time = timezone.now() - timedelta(hours=hours_ago)

            AlarmHistory.objects.create(
                device=device,
                point=point,
                alarm_type=scenario["alarm_type"],
                severity=scenario["severity"],
                trigger_value=scenario["trigger_value"],
                threshold_value=scenario["threshold_value"],
                message=f"TEST: {scenario['message']}",
                triggered_at=triggered_time,
                is_active=True,
            )

            created_count += 1

            # Print progress
            if created_count % 5 == 0:
                self.stdout.write(f"Created {created_count} test anomalies...")

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {created_count} test anomaly records!"
            )
        )

        # Show summary
        high_count = AlarmHistory.objects.filter(
            alarm_type="anomaly_detected", severity="high"
        ).count()

        medium_count = AlarmHistory.objects.filter(
            alarm_type="anomaly_detected", severity="medium"
        ).count()

        self.stdout.write("Total anomalies in database:")
        self.stdout.write(f"  High severity: {high_count}")
        self.stdout.write(f"  Medium severity: {medium_count}")
        self.stdout.write(f"  Total: {high_count + medium_count}")
        self.stdout.write("")
        self.stdout.write("Now visit: http://127.0.0.1:8000/anomaly-dashboard/")
