"""
Django management command to create test anomaly data
for testing the anomaly dashboard display
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from discovery.models import AlarmHistory, BACnetDevice, BACnetPoint


class Command(BaseCommand):
    help = "Create test anomaly data for dashboard testing"

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

        # Sample anomaly scenarios
        anomaly_scenarios = [
            {
                "alarm_type": "anomaly_detected",
                "severity": "high",
                "trigger_value": "35.7",
                "threshold_value": "2.8",
                "message": (
                    "Temperature spike detected: 35.7°C exceeds normal range "
                    "(18-24°C). Z-score: 2.8"
                ),
            },
            {
                "alarm_type": "anomaly_detected",
                "severity": "medium",
                "trigger_value": "16.2",
                "threshold_value": "2.1",
                "message": (
                    "Temperature drop detected: 16.2°C below normal range. "
                    "Possible HVAC malfunction."
                ),
            },
            {
                "alarm_type": "anomaly_detected",
                "severity": "high",
                "trigger_value": "42.1",
                "threshold_value": "3.2",
                "message": (
                    "Critical temperature anomaly: 42.1°C detected. "
                    "Immediate attention required."
                ),
            },
            {
                "alarm_type": "anomaly_detected",
                "severity": "medium",
                "trigger_value": "27.8",
                "threshold_value": "2.3",
                "message": (
                    "Elevated temperature detected: 27.8°C above comfort zone. "
                    "Check HVAC settings."
                ),
            },
            {
                "alarm_type": "anomaly_detected",
                "severity": "high",
                "trigger_value": "13.4",
                "threshold_value": "2.9",
                "message": (
                    "Abnormally low temperature: 13.4°C. "
                    "Potential heating system failure."
                ),
            },
            {
                "alarm_type": "anomaly_detected",
                "severity": "medium",
                "trigger_value": "26.5",
                "threshold_value": "2.0",
                "message": (
                    "Temperature variance detected: 26.5°C sustained reading "
                    "outside normal pattern."
                ),
            },
            {
                "alarm_type": "anomaly_detected",
                "severity": "high",
                "trigger_value": "38.9",
                "threshold_value": "3.1",
                "message": (
                    "Overheating alert: 38.9°C in server room. "
                    "Risk of equipment damage."
                ),
            },
            {
                "alarm_type": "anomaly_detected",
                "severity": "medium",
                "trigger_value": "15.8",
                "threshold_value": "2.2",
                "message": (
                    "Sub-optimal temperature: 15.8°C may affect occupant "
                    "comfort and energy efficiency."
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
