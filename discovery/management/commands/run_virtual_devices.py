import signal
import time

import BAC0
from django.core.management.base import BaseCommand

from discovery.models import VirtualBACnetDevice


class Command(BaseCommand):
    help = "Run virtual BACnet device server"

    def __init__(self):
        super().__init__()
        self.running_devices = {}  # {device_id: bacnet_instance}
        self.shutdown = False

    def handle(self, *args, **options):
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        self.stdout.write(
            self.style.SUCCESS("Starting Virtual BACnet Device server...")
        )

        self.start_all_devices()

        try:
            while not self.shutdown:
                time.sleep(5)
                self.check_device_states()
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()

    def start_all_devices(self):
        """Start all virtual devices from database"""
        devices = VirtualBACnetDevice.objects.filter(is_running=True)

        for device in devices:
            self.start_device(device)

    def start_device(self, device):
        """Start a single virtual device"""
        try:
            self.stdout.write(f"Starting device {device.device_id}...")

            bacnet = BAC0.lite(deviceId=device.device_id, port=device.port)

            self.running_devices[device.device_id] = bacnet
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Device {device.device_id} started on port {device.port}"
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Failed to start device {device.device_id}: {e}")
            )
            device.is_running = False
            device.save()

    def check_device_states(self):
        """Check if new devices should be started or stopped"""
        should_run = set(
            VirtualBACnetDevice.objects.filter(is_running=True).values_list(
                "device_id", flat=True
            )
        )

        currently_running = set(self.running_devices.keys())

        # Start new devices
        to_start = should_run - currently_running
        for device_id in to_start:
            device = VirtualBACnetDevice.objects.get(device_id=device_id)
            self.start_device(device)

        # Stop removed devices
        to_stop = currently_running - should_run
        for device_id in to_stop:
            self.stop_device(device_id)

    def stop_device(self, device_id):
        """Stop a single virtual devivce"""
        if device_id in self.running_devices:
            self.stdout.write(f"Stopping device {device_id}...")
            self.running_devices[device_id].disconnect()
            del self.running_devices[device_id]
            self.stdout.write(self.style.SUCCESS(f"✓ Device {device_id} stopped"))

    def cleanup(self):
        """Stop all running devices"""
        self.stdout.write(self.style.WARNING("\nShutting down..."))

        for device_id in list(self.running_devices.keys()):
            self.stop_device(device_id)

        self.stdout.write(self.style.SUCCESS("✓ All devices stopped"))

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.shutdown = True
