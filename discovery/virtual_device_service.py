"""
Virtual Device Service Layer

Handles creation, deletion, and management of virtual BACnet devices
"""

import logging

from .models import VirtualBACnetDevice

logger = logging.getLogger(__name__)


class VirtualDeviceService:
    """Service for managing virtual BACnet devices"""

    @staticmethod
    def create_virtual_device(device_id, device_name, description="", port=47808):
        """
        Create a virtual device in database

        Args:
            device_id (int): unique BACnet device ID
            device_name (str): Human-readable name
            description (str): Optional description
            port (int): BACnet port (default 47808)

        Returns:
            VirtualBACnet Devices: Created device instance

        Raises:
            ValueError: If device_id already exists
        """

        # Check if device_id already exists
        if VirtualBACnetDevice.objects.filter(device_id=device_id).exists():
            raise ValueError(f"Device ID {device_id} already exists")

        # Create device in database
        device = VirtualBACnetDevice.objects.create(
            device_id=device_id,
            device_name=device_name,
            description=description,
            port=port,
            is_running=True,
        )

        logger.info(f"Virtual device created: {device_id} - {device_name}")
        return device

    @staticmethod
    def delete_virtual_device(device_id):
        """
        Delete a virtual device

        Args:
            device_id (int): Device ID to delete

        Returns:
            bool: True if deleted, False if not found
        """
        try:
            device = VirtualBACnetDevice.objects.get(device_id=device_id)
            device.is_running = False
            device.save()
            device.delete()

            logger.info(f"Virtual device deleted: {device_id}")
            return True
        except VirtualBACnetDevice.DoesNotExist:
            logger.warning(f"Device {device_id} not found")
            return False

    @staticmethod
    def start_virtual_device(device_id):
        """
        Mark device as should be running
        Management command will pick it up within 5 seconds

        Args:
            device_id (int): Device ID to start

        Returns:
            bool: True if started, False if not found
        """
        try:
            device = VirtualBACnetDevice.objects.get(device_id=device_id)
            device.is_running = True
            device.save()
            logger.info(f"Virtual device marked for start: {device_id}")
            return True
        except VirtualBACnetDevice.DoesNotExist:
            return False

    @staticmethod
    def stop_virtual_device(device_id):
        """
        Mark device as should be stopped

        Args:
            device_id (int): Device ID to stop

        Returns:
            bool: True if stopped, False if not found
        """
        try:
            device = VirtualBACnetDevice.objects.get(device_id=device_id)
            device.is_running = False
            device.save()
            logger.info(f"Virtual device marked for stop: {device_id}")
            return True
        except VirtualBACnetDevice.DoesNotExist:
            return False

    @staticmethod
    def get_all_devices():
        """Get all virtual devices"""
        return VirtualBACnetDevice.objects.all().order_by("device_id")

    @staticmethod
    def get_running_devices():
        """Get all running virtual devices"""
        return VirtualBACnetDevice.objects.filter(is_running=True)
