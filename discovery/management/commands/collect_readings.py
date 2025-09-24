from django.core.management.base import BaseCommand

from discovery.services import BACnetService


class Command(BaseCommand):
    help = "Collect readings from all BACnet devices"

    def add_arguments(self, parser):
        parser.add_argument(
            "--devices",
            type=str,
            help="Comma-separated device IDs to collect from (default: all)",
        )

    def handle(self, *args, **options):
        self.stdout.write("🔄 Starting readings collection...")

        try:
            service = BACnetService()

            if options["devices"]:
                device_ids = [int(id.strip()) for id in options["devices"].split(",")]
                self.stdout.write(f"📋 Collecting from specific devices: {device_ids}")
                # TODO: Implement device-specific collection if needed
                results = service.collect_all_readings()
            else:
                results = service.collect_all_readings()

            self.stdout.write(self.style.SUCCESS("✅ Readings collection completed"))

            self.stdout.write(
                f"📈 Readings collected: {results.get('readings_collected', 0)}"
            )
            self.stdout.write(
                f"🎯 Devices successful: {results.get('devices_successful', 0)}"
            )
            self.stdout.write(f"❌ Devices failed: {results.get('devices_failed', 0)}")

            return (
                f"Completed: {results.get('readings_collected', 0)} readings collected "
                f"from {results.get('devices_successful', 0)} devices"
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Readings collection failed: {e}"))
            raise e
