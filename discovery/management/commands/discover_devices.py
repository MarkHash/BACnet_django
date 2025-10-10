from django.apps import apps
from django.core.management.base import BaseCommand


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
            # Use unified service from app config
            discovery_app = apps.get_app_config("discovery")
            service = discovery_app.bacnet_service
            mock_mode = options.get("mock", False)

            if mock_mode:
                self.stdout.write("⚠️ Mock mode not yet supported in unified service")
                devices = []
            else:
                devices = service.discover_devices()

            if devices is not None:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Device discovery completed: {len(devices)} devices found"
                    )
                )

                for device_info in devices:
                    if isinstance(device_info, dict):
                        device_id = device_info.get("device_id")
                        ip_addr = device_info.get("ip_address")
                        self.stdout.write(f"📡 Found device: {device_id} at {ip_addr}")
                    else:
                        self.stdout.write(f"📡 Found device: {device_info}")
            else:
                self.stdout.write(
                    self.style.WARNING("⚠️ Device discovery returned no results")
                )

            return f"Completed: {len(devices) if devices else 0} devices found"

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Device discovery failed: {e}"))
            raise e
