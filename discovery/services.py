import logging
import os

import BAC0
from django.utils import timezone

from .constants import BACnetConstants
from .exceptions import (
    BACnetBatchReadError,
    BACnetConnectionError,
    BACnetDeviceError,
    BACnetPropertyReadError,
    BACnetServiceError,
)
from .models import BACnetDevice, BACnetPoint, BACnetReading, DeviceStatusHistory

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s = %(levelname)s - %(message)s"
)

logging.getLogger("BAC0_Root").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

MAX_BATCH_SIZE = 50


class BACnetService:
    def __init__(self, callback=None):
        """
        BACnetService initialisation.

        Args:
            callback (function): callback function
        """
        self.bacnet = None
        self.callback = callback

    def __enter__(self):
        if self.bacnet is not None:
            self._log("🔄 Using existing BACnet connection")
            return self

        if self._connect():
            return self
        raise BACnetConnectionError("Failed to connect to BACnet")

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._disconnect()
        return False

    @staticmethod
    def requires_connection(func):
        def wrapper(self, *args, **kwargs):
            if not self.bacnet:
                raise ConnectionError("BACnet not connected")
            return func(self, *args, **kwargs)

        return wrapper

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

            # Use specific IP if provided in environment
            bacnet_ip = os.getenv("BACNET_IP")
            if bacnet_ip:
                self._log(f"🎯 Using specified IP: {bacnet_ip}")

                # Parse IP and port from BACNET_IP (format: IP:PORT/MASK)
                if ":" in bacnet_ip and "/" in bacnet_ip:
                    # Extract IP, port, and mask from "192.168.1.5:47809/24"
                    ip_part, mask_part = bacnet_ip.split("/")
                    ip_address, port = ip_part.split(":")
                    ip_with_mask = f"{ip_address}/{mask_part}"
                    port = int(port)
                    self._log(f"🔧 Parsed - IP: {ip_with_mask}, Port: {port}")

                    self.bacnet = BAC0.lite(ip=ip_with_mask, port=port)
                else:
                    # Fallback to original format
                    self.bacnet = BAC0.lite(ip=bacnet_ip)
            else:
                self._log("🔍 Auto-detecting network interface")
                self.bacnet = BAC0.lite()

            self._log("✅ Connected successfully")

            return True

        except (OSError, ConnectionError) as e:
            raise BACnetConnectionError(f"Network connection failed: {e}")
        except Exception as e:
            raise BACnetConnectionError(f"Network connection failed: {e}")

    def _disconnect(self):
        """
        Disconnect from BACnet with enhanced cleanup.

        Raises:
            Exception: BACnet connection errors

        """
        try:
            self._log("🔌 Disconnecting...")
            if self.bacnet:
                # Enhanced cleanup for port release
                try:
                    # Stop all tasks first
                    if (
                        hasattr(self.bacnet, "task_manager")
                        and self.bacnet.task_manager
                    ):
                        self.bacnet.task_manager.stop()
                except Exception as e:
                    logger.debug(f"Task manager stop error (harmless): {e}")

                # Disconnect BAC0
                self.bacnet.disconnect()

                # Force garbage collection to help release resources
                import gc

                gc.collect()

                # Add small delay to ensure port is released
                import time

                time.sleep(0.1)

            self.bacnet = None

        except (OSError, AttributeError) as e:
            logger.debug(f"Cleanup error during disconnect (harmless): {e}")
        except Exception as e:
            logger.debug(f"Other cleanup error (harmless): {e}")
        finally:
            # Ensure bacnet is set to None regardless
            self.bacnet = None

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
            with self:
                self._log("🔍 Starting device discovery...")
                devices = self.bacnet.discover()

                if devices is not None:
                    existing_device_ids = set(
                        BACnetDevice.objects.filter(
                            device_id__in=[device_info[1] for device_info in devices]
                        ).values_list("device_id", flat=True)
                    )
                    devices_to_create = []
                    history_records = []
                    for device_info in devices:
                        device_id = device_info[1]
                        if device_id not in existing_device_ids:
                            devices_to_create.append(
                                BACnetDevice(
                                    device_id=device_id,
                                    address=str(device_info[0]),
                                    vendor_id=getattr(
                                        device_info,
                                        BACnetConstants.VENDOR_IDENTIFIER,
                                        0,
                                    ),
                                    is_online=True,
                                    last_seen=timezone.now(),
                                )
                            )
                    existing_devices = BACnetDevice.objects.filter(
                        device_id__in=existing_device_ids
                    )
                    device_info_map = {
                        device_info[1]: device_info for device_info in devices
                    }

                    for device in existing_devices:
                        device_info = device_info_map[device.device_id]
                        device.address = str(device_info[0])
                        device.is_online = True
                        device.is_active = True
                        device.last_seen = timezone.now()

                    if devices_to_create:
                        BACnetDevice.objects.bulk_create(devices_to_create)

                    if existing_devices:
                        BACnetDevice.objects.bulk_update(
                            existing_devices,
                            fields=["address", "is_online", "is_active", "last_seen"],
                        )

                    all_devices = BACnetDevice.objects.filter(
                        device_id__in=[device_info[1] for device_info in devices]
                    )
                    history_records = [
                        DeviceStatusHistory(
                            device=device, is_online=True, timestamp=timezone.now()
                        )
                        for device in all_devices
                    ]

                    DeviceStatusHistory.objects.bulk_create(history_records)

                    self._log(f"✅ Found {len(devices)} devices (real)")
                else:
                    self._log("✅ Found 0 devices")

                return devices
        except (OSError, ConnectionError) as e:
            raise BACnetConnectionError(f"Device discovery connection failed: {e}")
        except Exception as e:
            logger.error(f"Device discovery failed: {e}")
            raise BACnetServiceError(f"Device discovery failed: {e}")

    def read_device_property(self, device, property_name):
        try:
            read_string = f"{device.address} device {device.device_id} {property_name}"
            return self.bacnet.read(read_string)

        except (OSError, AttributeError) as e:
            raise BACnetPropertyReadError(device.device_id, property_name, e)
        except Exception as e:
            self._log(f"⚠️ Could not read {property_name} from {device.device_id}: {e}")
            raise BACnetPropertyReadError(device.device_id, property_name, e)

    def discover_device_points(self, device):
        """
        Discover points on a device and save to database as BACnetPoint records.


        """
        try:
            with self:
                vendor_id = self.read_device_property(
                    device, BACnetConstants.VENDOR_IDENTIFIER
                )
                if vendor_id:
                    device.vendor_id = vendor_id
                    device.save()
                    self._log(f"📋 Updated vendor ID: {vendor_id}")

                point_list = self.read_device_property(
                    device, BACnetConstants.OBJECT_LIST
                )

                for point in point_list:
                    try:
                        self._log(f"Creating point: {point}")
                        self._log(
                            f"Point attributes: object_type={point[0]},"
                            f" instance={point[1]}"
                        )
                        object_type = point[0]
                        instance_number = point[1]

                        BACnetPoint.objects.get_or_create(
                            device=device,
                            object_type=object_type,
                            instance_number=instance_number,
                            identifier=f"{object_type}:{instance_number}",
                            # defaults={
                            #     value_last_read=timezone.now()
                            # }
                        )
                    except Exception as e:
                        logger.error(f"Error {e}")
                        self._log(f"Failed point data: {point}")

                device.points_read = True
                device.save()

                return point_list

        except BACnetPropertyReadError as e:
            raise BACnetDeviceError(device.device_id, f"Point discovery failed: {e}", e)
        except (OSError, ConnectionError) as e:
            raise BACnetDeviceError(
                device.device_id, "Point discovery connection failed", e
            )
        except Exception as e:
            logger.error(f"Point discovery failed for device {device.device_id}: {e}")
            raise BACnetDeviceError(device.device_id, f"Point discovery failed: {e}", e)

    def read_point_value(self, device, point):
        """
        Get the current value of a known point
        Args:
            device (object): device object
            point (object): point object
        """
        try:
            with self:
                read_string = (
                    f"{device.address} {point.object_type} "
                    f"{point.instance_number} {BACnetConstants.PRESENT_VALUE}"
                )
                self._log(f"📖 Reading {point.identifier}")
                value = self.bacnet.read(read_string)

                return value

        except BACnetConnectionError:
            raise
        except (OSError, ConnectionError) as e:
            raise BACnetDeviceError(
                device.device_id, f"Failed to read point {point.identifier}", e
            )
        except Exception as e:
            logger.error(
                f"Failed to read point {point.identifier} "
                f"from device {device.device_id}: {e}"
            )
            raise BACnetDeviceError(
                device.device_id, f"Failed to read point {point.identifier}", e
            )

    def _read_single_point(self, device, point, results):
        try:
            read_string = (
                f"{device.address} {point.object_type} "
                f"{point.instance_number} {BACnetConstants.PRESENT_VALUE}"
            )
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

    def read_device_points(self, device, results):
        try:
            self._log(f"📖 Reading from device {device.device_id}")
            readable_points = device.points.filter(
                object_type__in=BACnetConstants.READABLE_OBJECT_TYPES
            )

            if not self._read_device_points_batch(device, readable_points, results):
                for point in readable_points:
                    self._read_single_point(device, point, results)

        except Exception as e:
            results["devices_failed"] += 1
            self._log(f"❌ Device {device.device_id} failed: {e}")

    def _build_batch_request(self, device, points_list):
        request_parts = [device.address]

        for point in points_list:
            request_parts.extend(
                [
                    point.object_type,
                    str(point.instance_number),
                    BACnetConstants.PRESENT_VALUE,
                    BACnetConstants.OBJECT_NAME,
                ]
            )
            if point.object_type in BACnetConstants.ANALOG_OBJECT_TYPES:
                request_parts.append(BACnetConstants.UNITS)
        return request_parts

    def _calculate_expected_values(self, points_list):
        expected_values = 0
        for point in points_list:
            if point.object_type in BACnetConstants.ANALOG_OBJECT_TYPES:
                expected_values += 3
            else:
                expected_values += 2
        return expected_values

    def _process_batch_results(self, points_list, values, results):
        value_index = 0
        for point in points_list:
            present_value = values[value_index]
            object_name = values[value_index + 1]

            if point.object_type in BACnetConstants.ANALOG_OBJECT_TYPES:
                units = values[value_index + 2]
                value_index += 3
            else:
                units = None
                value_index += 2

            if present_value is not None:
                BACnetReading.objects.create(
                    point=point,
                    value=str(present_value),
                    read_time=timezone.now(),
                )
                point.present_value = str(present_value)
                if object_name:
                    point.object_name = str(object_name)
                if units:
                    point.units = str(units)
                point.value_last_read = timezone.now()
                point.save()
                results["readings_collected"] += 1
        return results

    def _execute_batch_read(self, device, points_list, results):
        try:
            request_parts = self._build_batch_request(device, points_list)
            batch_request = " ".join(request_parts)
            values = self.bacnet.readMultiple(batch_request)

            expected_values = self._calculate_expected_values(points_list)

            if values and len(values) == expected_values:
                self._log(f"✅ Batch read successful: {len(values)} values")

                self._process_batch_results(points_list, values, results)
                return True
            else:
                self._log(
                    f"⚠️ Batch read mismatch: got {len(values) if values else 0} "
                    f"values for {len(points_list)} points"
                )
            return False
        except (OSError, ConnectionError) as e:
            raise BACnetBatchReadError(device.device_id, len(points_list), e)
        except Exception as e:
            self._log(f"❌ Batch read failed: {e}")
            raise BACnetBatchReadError(device.device_id, len(points_list), e)

    def _read_device_points_in_chunks(self, device, points_list, results):
        try:
            chunk_size = MAX_BATCH_SIZE
            total_chunks = (len(points_list) + chunk_size - 1) // chunk_size
            self._log(
                f"📦 Large device: splitting {len(points_list)} "
                f"points into {total_chunks} chunks of {chunk_size}"
            )

            for i in range(0, len(points_list), chunk_size):
                chunk = points_list[i : i + chunk_size]
                self._log(
                    f"📦 Processing chunk {i//chunk_size + 1}/{total_chunks} "
                    f"({len(chunk)} points)"
                )

                try:
                    if not self._read_single_batch_chunk(device, chunk, results):
                        self._log(
                            f"⚠️ Chunk {i//chunk_size + 1} failed, falling back to "
                            f"individual reads"
                        )

                        for point in chunk:
                            self._read_single_point(device, point, results)
                except BACnetBatchReadError as e:
                    self._log(f"⚠️ Chunk {i//chunk_size + 1} failed: {e}")

            return True
        except (OSError, ConnectionError) as e:
            raise BACnetDeviceError(
                device.device_id, "Chunked read connection failed", e
            )
        except Exception as e:
            self._log(f"❌ Chunked batch read failed: {e}")
            raise BACnetDeviceError(device.device_id, "Chunked read failed", e)

    def _read_single_batch_chunk(self, device, chunk_points, results):
        points_list = list(chunk_points)
        return self._execute_batch_read(device, points_list, results)

    def _read_device_points_batch(self, device, readable_points, results):
        points_list = list(readable_points)

        if len(points_list) > MAX_BATCH_SIZE:
            return self._read_device_points_in_chunks(device, points_list, results)

        return self._execute_batch_read(device, points_list, results)

    def _initialise_results(self):
        return {
            "devices_processed": 0,
            "readings_collected": 0,
            "devices_failed": 0,
            "timestamp": timezone.now(),
        }

    def _get_online_devices(self):
        online_devices = BACnetDevice.objects.filter(is_online=True)
        self._log(f"📊 Found {online_devices.count()} online devices")
        return online_devices

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
        results = self._initialise_results()
        online_devices = self._get_online_devices()

        with self:
            for device in online_devices:
                self.read_device_points(device, results)
                results["devices_processed"] += 1

            self._log(
                f"✅ Collected {results['readings_collected']} readings "
                f"from {results['devices_processed']} devices"
            )
            return results
