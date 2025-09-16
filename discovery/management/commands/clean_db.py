from django.core.management.base import BaseCommand

from discovery.models import BACnetDevice, BACnetPoint, BACnetReading


class Command(BaseCommand):
    help = "Clean all BACnet data from database"

    def handle(self, *args, **options):
        reading_count = BACnetReading.objects.count()
        point_count = BACnetPoint.objects.count()
        device_count = BACnetDevice.objects.count()

        BACnetReading.objects.all().delete()
        BACnetPoint.objects.all().delete()
        BACnetDevice.objects.all().delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Cleaned {reading_count} readings, {point_count} points,"
                f" {device_count} devices"
            )
        )
