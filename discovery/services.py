import logging

import BAC0
from django.utils import timezone

from .models import BACnetDevice, BACnetReading, DeviceStatusHistory

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s = %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BACnetService:
    def __init__(self, callback=None):
        """
        BACnetService initialisation.

        Args:
            callback (function): callback function
        """
        self.bacnet = None
        self.callback = callback

    def _connect(self):
        """
        Connect to BACnet.

        Returns:
            Boolean: True/False if it can connect to BACnet

        Raises:
            Exception: BACnet connection errors

        """
        try:
            self._log("🔌 Connecting to BACnet...")
            self.bacnet = BAC0.connect()
            self._log("✅ Connected successfully")

            return True

        except Exception as e:
            logger.error(f"Error: {e}")
            return False

    def _disconnect(self):
        """
        Disconnect to BACnet.

        Raises:
            Exception: BACnet connection errors

        """
        try:
            self._log("🔌 Disconnecting...")
            if self.bacnet:
                self.bacnet.disconnect()

        except (OSError, AttributeError) as e:
            logger.debug(f"Cleanup error during disconnect (harmless): {e}")

        except Exception as e:
            logger.error(f"Error: {e}")

    def _log(self, message, level="info"):
        """
        Log message and optionally call callback for interactive mode.

        Args:
            message (str): Message to log and send to callback
            level (str): Log level (default: "info")
        """
        getattr(logger, level)(message)
        if self.callback:
            self.callback(message)

    def discover_devices(self, network="192.168.1.0/24", timeout=10, mock_mode=False):
        """
        Discover BACnet devices on the network and save to database.
        Args:
            network (str): Network range to scan (default: "192.168.1.0/24")
            timeout (int): Discovery timeout in seconds (default: 10)
            mock_mode (bool): Use mock data for testing (default: False)

        Returns:
            list: List of discovered device dictionaries with deviceId,
            address, vendorId

        Raises:
            Exception: BACnet connection or database errors

        """
        try:
            if mock_mode:
                # Mock data for testing Django integration
                self._log("🔍 Starting device discovery (MOCK MODE)...")
                devices = [
                    {"deviceId": 123, "address": "192.168.1.100", "vendorId": 15},
                    {"deviceId": 456, "address": "192.168.1.101", "vendorId": 25},
                ]

                for device_info in devices:
                    device, created = BACnetDevice.objects.get_or_create(
                        device_id=device_info["deviceId"],
                        defaults={
                            "address": str(device_info["address"]),
                            "vendor_id": device_info["vendorId"],
                            "is_online": True,
                            "last_seen": timezone.now(),
                        },
                    )

                    DeviceStatusHistory.objects.create(
                        device=device, is_online=True, timestamp=timezone.now()
                    )

                    self._log(
                        f"{'Created' if created else 'Updated'} device "
                        f"{device_info['deviceId']}"
                    )
                self._log(f"✅ Found {len(devices)} devices (mock)")

                return devices

            # Real BAC0 discovery
            if self._connect():
                self._log("🔍 Starting device discovery...")
                devices = self.bacnet.discover()

                if devices is not None:
                    for device_info in devices:
                        device, created = BACnetDevice.objects.get_or_create(
                            device_id=device_info["deviceId"],
                            defaults={
                                "address": str(device_info["address"]),
                                "vendor_id": device_info["vendorId"],
                                "is_online": True,
                                "last_seen": timezone.now(),
                            },
                        )

                        DeviceStatusHistory.objects.create(
                            device=device, is_online=True, timestamp=timezone.now()
                        )

                        self._log(
                            f"{'Created' if created else 'Updated'} device "
                            f"{device_info['deviceId']}"
                        )
                    self._log(f"✅ Found {len(devices)} devices (real)")
                else:
                    self._log("✅ Found 0 devices")

                self._disconnect()
                return devices

        except Exception as e:
            logger.error(f"Error: {e}")

    # def read_all_device_points(self, device_id):
    #     try:
    #         if self._connect():
    #             devices = self.discover_devices()
    #             for device in devices:
    #                 device.read('device:X objectList')

    #             self._disconnect()

    #     except Exception as e:
    #         logger.error(f"Error: {e}")

    def collect_all_readings(self):
        """
        Collect current readings from all online BACnet devices
        and save to database.

        Returns:
            dict: Summary of collection results with devices_processed,
            readings_collected, etc.

        Raises:
            Exception: BACnet connection or database errors

        """
        try:
            results = {
                "devices_processed": 0,
                "readings_collected": 0,
                "devices_failed": 0,
                "timestamp": timezone.now(),
            }
            online_devices = BACnetDevice.objects.filter(is_online=True)
            self._log(f"📊 Found {online_devices.count()} online devices")
            if self._connect():
                for device in online_devices:
                    try:
                        self._log(f"📖 Reading from device {device.device_id}")
                        readable_points = device.points.filter(
                            object_type__in=["analogInput", "analogOutput"]
                        )

                        for point in readable_points:
                            try:
                                read_string = f"{device.address} "
                                f"{point.object_type} {point.instance_number} "
                                "presentValue"
                                self._log(f"📖 Reading {point.identifier}")
                                value = self.bacnet.read(read_string)

                                if value is not None:
                                    BACnetReading.objects.create(
                                        point=point,
                                        value=str(value),
                                        read_time=timezone.now(),
                                    )
                                    results["readings_collected"] += 1

                            except Exception as e:
                                self._log(f"❌ Failed to read {point.identifier}: {e}")
                        results["devices_processed"] += 1
                    except Exception as e:
                        results["devices_failed"] += 1
                        self._log(f"❌ Device {device.device_id} failed: {e}")

                self._disconnect()
                self._log(
                    f"✅ Collected {results['readings_collected']} readings "
                    f"from {results['devices_processed']} devices"
                )
                return results

        except Exception as e:
            logger.error(f"Error: {e}")
            return None

        # def check_device_health(self):
        #     try:
        #         if self._connect():
        #             devices = self.discover_devices()

        #             self._disconnect()

        except Exception as e:
            logger.error(f"Error: {e}")
