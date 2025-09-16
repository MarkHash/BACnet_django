import logging

import BAC0
from django.utils import timezone

from .constants import BACnetConstants
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
                        # print(f"Device structure: {device_info}")
                        # print(f"Type: {type(device_info)}")
                        # print(f"Dir: {dir(device_info)}")
                        device, created = BACnetDevice.objects.get_or_create(
                            device_id=device_info[1],
                            defaults={
                                "address": str(device_info[0]),
                                "vendor_id": getattr(
                                    device_info, "vendorIdentifier", 0
                                ),
                                "is_online": True,
                                "is_active": True,
                                "last_seen": timezone.now(),
                            },
                        )

                        if not created:
                            device.address = str(device_info[0])
                            device.is_online = True
                            device.is_active = True
                            device.last_seen = timezone.now()
                            device.save()

                        DeviceStatusHistory.objects.create(
                            device=device, is_online=True, timestamp=timezone.now()
                        )

                        self._log(
                            f"{'Created' if created else 'Updated'} device "
                            f"{device_info[1]}"
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

    def read_device_property(self, device, property_name):
        try:
            read_string = f"{device.address} device {device.device_id} {property_name}"
            return self.bacnet.read(read_string)

        except Exception as e:
            self._log(f"⚠️ Could not read {property_name}: {e}")
            return None

    def discover_device_points(self, device):
        """
        Discover points on a device and save to database as BACnetPoint records.


        """
        try:
            if self._connect():
                vendor_id = self.read_device_property(device, "vendorIdentifier")
                if vendor_id:
                    device.vendor_id = vendor_id
                    device.save()
                    self._log(f"📋 Updated vendor ID: {vendor_id}")

                point_list = self.read_device_property(device, "objectList")

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

                self._disconnect()
                return point_list

        except Exception as e:
            logger.error(f"Error: {e}")
            return None

    def read_point_value(self, device, point):
        """
        Get the current value of a known point
        Args:
            device (object): device object
            point (object): point object
        """
        try:
            if self._connect():
                read_string = (
                    f"{device.address} {point.object_type} "
                    f"{point.instance_number} presentValue"
                )
                self._log(f"📖 Reading {point.identifier}")
                value = self.bacnet.read(read_string)

                self._disconnect()
                return value

        except Exception as e:
            logger.error(f"Error: {e}")
            return None

    def _read_single_point(self, device, point, results):
        try:
            read_string = (
                f"{device.address} {point.object_type} "
                f"{point.instance_number} presentValue"
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

                if not self._read_single_batch_chunk(device, chunk, results):
                    self._log(
                        f"⚠️ Chunk {i//chunk_size + 1} failed, falling back to "
                        f"individual reads"
                    )

                    for point in chunk:
                        self._read_single_point(device, point, results)
            return True
        except Exception as e:
            self._log(f"❌ Chunked batch read failed: {e}")
            return False

    def _read_single_batch_chunk(self, device, chunk_points, results):
        try:
            request_parts = [device.address]
            points_list = list(chunk_points)

            for point in points_list:
                request_parts.extend(
                    [
                        point.object_type,
                        str(point.instance_number),
                        "presentValue",
                        "objectName",
                    ]
                )
                if point.object_type in ["analogInput", "analogOutput", "analogValue"]:
                    request_parts.append("units")

            batch_request = " ".join(request_parts)
            values = self.bacnet.readMultiple(batch_request)

            expected_values = 0
            for point in points_list:
                if point.object_type in ["analogInput", "analogOutput", "analogValue"]:
                    expected_values += 3
                else:
                    expected_values += 2

            if values and len(values) == expected_values:
                self._log(f"✅ Batch read successful: {len(values)} values")

                value_index = 0
                for point in points_list:
                    present_value = values[value_index]
                    object_name = values[value_index + 1]

                    if point.object_type in [
                        "analogInput",
                        "analogOutput",
                        "analogValue",
                    ]:
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
                return True
            else:
                self._log(
                    f"⚠️ Batch read mismatch: got {len(values) if values else 0} "
                    f"values for {len(points_list)} points"
                )
            return False
        except Exception as e:
            self._log(f"❌ Batch read failed: {e}")
            return False

    def _read_device_points_batch(self, device, readable_points, results):
        try:
            self._log(f"📦 Batch reading {len(readable_points)} points")
            request_parts = [device.address]
            points_list = list(readable_points)

            if len(points_list) > MAX_BATCH_SIZE:
                return self._read_device_points_in_chunks(device, points_list, results)

            for point in points_list:
                request_parts.extend(
                    [
                        point.object_type,
                        str(point.instance_number),
                        "presentValue",
                        "objectName",
                    ]
                )
                if point.object_type in ["analogInput", "analogOutput", "analogValue"]:
                    request_parts.append("units")

            batch_request = " ".join(request_parts)
            values = self.bacnet.readMultiple(batch_request)

            expected_values = 0
            for point in points_list:
                if point.object_type in ["analogInput", "analogOutput", "analogValue"]:
                    expected_values += 3
                else:
                    expected_values += 2

            if values and len(values) == expected_values:
                self._log(f"✅ Batch read successful: {len(values)} values")

                value_index = 0
                for point in points_list:
                    present_value = values[value_index]
                    object_name = values[value_index + 1]

                    if point.object_type in [
                        "analogInput",
                        "analogOutput",
                        "analogValue",
                    ]:
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
                return True
            else:
                self._log(
                    f"⚠️ Batch read mismatch: got {len(values) if values else 0} "
                    f"values for {len(points_list)} points"
                )
            return False
        except Exception as e:
            self._log(f"❌ Batch read failed: {e}")
            return False

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
        if self._connect():
            try:
                for device in online_devices:
                    self.read_device_points(device, results)
                    results["devices_processed"] += 1

                self._log(
                    f"✅ Collected {results['readings_collected']} readings "
                    f"from {results['devices_processed']} devices"
                )
                return results
            finally:
                self._disconnect()
        return None

        # def check_device_health(self):
        #     try:
        #         if self._connect():
        #             devices = self.discover_devices()

        #             self._disconnect()
