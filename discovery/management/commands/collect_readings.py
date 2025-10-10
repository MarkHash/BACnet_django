from django.apps import apps
from django.core.management.base import BaseCommand


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
            # Use unified service from app config
            discovery_app = apps.get_app_config("discovery")
            discovery_app.bacnet_service

            if options["devices"]:
                device_ids = [int(id.strip()) for id in options["devices"].split(",")]
                self.stdout.write(f"📋 Collecting from specific devices: {device_ids}")
                # TODO: Implement device-specific collection if needed
                results = {
                    "readings_collected": 0,
                    "devices_successful": 0,
                    "devices_failed": 0,
                }
                self.stdout.write(
                    "⚠️ Device-specific collection not yet implemented in "
                    "unified service"
                )
            else:
                # TODO: Implement collect_all_readings in unified service
                results = {
                    "readings_collected": 0,
                    "devices_successful": 0,
                    "devices_failed": 0,
                }
                self.stdout.write(
                    "⚠️ Reading collection not yet implemented in unified service"
                )

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
