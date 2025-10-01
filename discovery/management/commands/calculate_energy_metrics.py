from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from discovery.energy_analytics import EnergyAnalyticsService


class Command(BaseCommand):
    help = "Calculate energy metrics from BACnet temperature data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days-back", type=int, default=1, help="Calculate metrics for last N days"
        )

    def handle(self, *args, **options):
        service = EnergyAnalyticsService()

        days_back = options["days_back"]
        total_metrics = 0

        for i in range(days_back):
            date = timezone.now().date() - timedelta(days=i)
            count = service.calculate_daily_metrics(date)
            total_metrics += count
            self.stdout.write(f"Date {date}: processed {count} devices")

        self.stdout.write(
            self.style.SUCCESS(f"Total devices processed: {total_metrics}")
        )
