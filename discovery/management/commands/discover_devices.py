from django.core.management.base import BaseCommand

from discovery.services import BACnetService


class Command(BaseCommand):
    help = "Discover BACnet devices on the network"

    def add_arguments(self, parser):
        parser.add_argument(
            "--mock",
            action="store_true",
            help="Use mock mode for testing",
        )

    def handle(self, *args, **options):
        self.stdout.write("🔍 Starting device discovery...")

        try:
            service = BACnetService()
            mock_mode = options.get("mock", False)

            if mock_mode:
                self.stdout.write("⚠️ Using mock mode")

            devices = service.discover_devices(mock_mode=mock_mode)

            if devices is not None:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Device discovery completed: {len(devices)} devices found"
                    )
                )

                for device_info in devices:
                    self.stdout.write(
                        f"📡 Found device: {device_info[1]} at {device_info[0]}"
                    )
            else:
                self.stdout.write(
                    self.style.WARNING("⚠️ Device discovery returned no results")
                )

            return f"Completed: {len(devices) if devices else 0} evices found"

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Device discovery failed: {e}"))
            raise e
