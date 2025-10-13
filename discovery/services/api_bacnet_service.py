"""
API-Based BACnet Service

This service communicates with the BACnet API service (FastAPI) running on
the host network. It replaces direct BAC0 usage with HTTP API calls.

Architecture:
    Django Views → ApiBACnetService → BACnetAPIClient (HTTP) → BACnet API Service → BAC0
"""

import logging
from typing import Dict, List, Optional

from django.utils import timezone

from discovery.bacnet_api_client import get_bacnet_api_client
from discovery.models import BACnetDevice, BACnetPoint

logger = logging.getLogger(__name__)


class ApiBACnetService:
    """BACnet service using HTTP API client"""

    def __init__(self):
        self.api_client = get_bacnet_api_client()

    def discover_devices(self) -> List[Dict]:
        """
        Discover BACnet devices on the network

        Returns:
            List of discovered devices with device_id, ip_address, port
        """
        try:
            logger.info("Starting BACnet device discovery via API...")
            devices = self.api_client.discover_devices()

            # Save discovered devices to database
            for device_data in devices:
                device_id = device_data.get("device_id")
                ip_address = device_data.get("ip_address")

                if device_id and ip_address:
                    device, created = BACnetDevice.objects.update_or_create(
                        device_id=device_id,
                        defaults={
                            "ip_address": ip_address,
                            "is_active": True,
                            "is_online": True,
                            "last_seen": timezone.now(),
                        },
                    )

                    if created:
                        logger.info(f"Created new device: {device_id} at {ip_address}")
                    else:
                        logger.info(f"Updated device: {device_id} at {ip_address}")

            logger.info(f"Discovery complete: {len(devices)} devices found")
            return devices

        except Exception as e:
            logger.error(f"Device discovery failed: {e}")
            return []

    def discover_device_points(self, device: BACnetDevice) -> Optional[List]:
        """
        Discover points/objects in a BACnet device

        Args:
            device: BACnetDevice instance

        Returns:
            List of discovered points or None
        """
        try:
            logger.info(f"Discovering points for device {device.device_id}...")
            points = self.api_client.discover_device_points(device.device_id)

            if points:
                # Save points to database
                for point_data in points:
                    object_type = point_data.get("object_type")
                    instance_number = point_data.get("instance_number")

                    if object_type and instance_number is not None:
                        point, created = BACnetPoint.objects.update_or_create(
                            device=device,
                            object_type=object_type,
                            instance_number=instance_number,
                            defaults={
                                "identifier": f"{object_type}:{instance_number}",
                                "object_name": point_data.get("object_name", ""),
                                "description": point_data.get("description", ""),
                                "units": point_data.get("units", ""),
                                "is_readable": True,
                            },
                        )

                        if created:
                            logger.debug(
                                f"Created point {object_type}:{instance_number} "
                                f"for device {device.device_id}"
                            )

                # Update device metadata
                device.points_read = True
                device.save(update_fields=["points_read"])

                logger.info(
                    f"Discovered {len(points)} points for device {device.device_id}"
                )
                return points

            return None

        except Exception as e:
            logger.error(f"Point discovery failed for device {device.device_id}: {e}")
            return None

    def read_point_value(
        self, device: BACnetDevice, point: BACnetPoint
    ) -> Optional[any]:
        """
        Read a single point value

        Args:
            device: BACnetDevice instance
            point: BACnetPoint instance

        Returns:
            Point value or None
        """
        try:
            value = self.api_client.read_point_value(
                device.device_id, point.object_type, point.instance_number
            )

            if value is not None:
                # Update point with new value
                point.present_value = str(value)
                point.value_last_read = timezone.now()
                point.save(update_fields=["present_value", "value_last_read"])

                logger.debug(
                    f"Read {point.identifier} from device {device.device_id}: {value}"
                )

            return value

        except Exception as e:
            logger.error(
                f"Failed to read {point.identifier} from device {device.device_id}: {e}"
            )
            return None

    def read_device_points(self, device: BACnetDevice, results: dict = None):
        """
        Read all points from a device

        Args:
            device: BACnetDevice instance
            results: Optional results dict to update

        Returns:
            Number of readings collected
        """
        if results is None:
            results = {"readings_collected": 0}

        try:
            points = device.points.filter(is_readable=True)
            readings_count = 0

            for point in points:
                value = self.read_point_value(device, point)
                if value is not None:
                    readings_count += 1

            results["readings_collected"] = readings_count
            logger.info(f"Read {readings_count} points from device {device.device_id}")

            return readings_count

        except Exception as e:
            logger.error(f"Failed to read points from device {device.device_id}: {e}")
            return 0

    def health_check(self) -> dict:
        """
        Check BACnet API service health

        Returns:
            Health status dict
        """
        try:
            return self.api_client.health_check()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}


# Singleton instance
_service = None


def get_api_bacnet_service() -> ApiBACnetService:
    """Get singleton API BACnet service instance"""
    global _service
    if _service is None:
        _service = ApiBACnetService()
    return _service
