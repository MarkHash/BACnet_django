"""
BACnet API Client for Django

This module provides a client to communicate with the BACnet API service
running on the host network. It handles all BACnet operations via HTTP API.

Architecture:
    Django Web App → BACnetAPIClient (HTTP) → BACnet API Service → BAC0 → BACnet Network

Usage:
    from discovery.bacnet_api_client import BACnetAPIClient

    client = BACnetAPIClient()
    devices = client.discover_devices()
    points = client.discover_device_points(device_id=2000)
    value = client.read_point_value(device_id=2000, point_id=123)
"""

import logging
from typing import Dict, List, Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class BACnetAPIClient:
    """Client for communicating with BACnet API service"""

    def __init__(self, api_url: str = None):
        """
        Initialize BACnet API client

        Args:
            api_url: Base URL of BACnet API service (default: http://localhost:5001)
        """
        self.api_url = api_url or getattr(
            settings, "BACNET_API_URL", "http://localhost:5001"
        )
        self.timeout = 30  # seconds

    def _make_request(
        self, method: str, endpoint: str, data: dict = None, timeout: int = None
    ) -> dict:
        """
        Make HTTP request to BACnet API service

        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint path
            data: Request payload (for POST)
            timeout: Request timeout in seconds

        Returns:
            Response JSON data

        Raises:
            requests.exceptions.RequestException: On request failure
        """
        url = f"{self.api_url}{endpoint}"
        timeout = timeout or self.timeout

        try:
            if method.upper() == "GET":
                response = requests.get(url, timeout=timeout)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, timeout=timeout)
            elif method.upper() == "DELETE":
                response = requests.delete(url, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            logger.error(f"Request timeout: {method} {url}")
            raise
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error: BACnet API service not reachable at {url}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {method} {url} - {e}")
            raise

    def health_check(self) -> dict:
        """
        Check BACnet API service health

        Returns:
            Health status dict with keys: status, bacnet_connected, local_ip, etc.
        """
        return self._make_request("GET", "/api/health")

    def discover_devices(self) -> List[Dict]:
        """
        Discover BACnet devices on the network

        Returns:
            List of discovered devices, each with: device_id, ip_address, port
            Example: [{'device_id': 2000, 'ip_address': '192.168.1.207', 'port': 47808}]
        """
        response = self._make_request("POST", "/api/discover", timeout=60)

        if response.get("success"):
            devices = response.get("devices", [])
            logger.info(f"Discovered {len(devices)} BACnet devices")
            return devices
        else:
            logger.warning("Device discovery failed")
            return []

    def discover_device_points(self, device_id: int) -> Optional[List[Dict]]:
        """
        Discover points/objects in a BACnet device

        Args:
            device_id: BACnet device ID

        Returns:
            List of points or None on failure
            Example: [{'object_type': 'analogInput', 'instance_number': 1, ...}]
        """
        response = self._make_request(
            "POST", f"/api/devices/{device_id}/points", timeout=60
        )

        if response.get("success"):
            points = response.get("points", [])
            logger.info(f"Discovered {len(points)} points for device {device_id}")
            return points
        else:
            logger.warning(f"Point discovery failed for device {device_id}")
            return None

    def read_point_value(
        self, device_id: int, object_type: str, instance_number: int
    ) -> Optional[dict]:
        """
        Read a single point value from a BACnet device

        Args:
            device_id: BACnet device ID
            object_type: BACnet object type (e.g., 'analogInput')
            instance_number: Object instance number

        Returns:
            Point data dict or None on failure
            Example: {'value': 72.5, 'units': 'degreesFahrenheit', ...}
        """
        response = self._make_request(
            "POST",
            "/api/points/read",
            data={
                "device_id": device_id,
                "object_type": object_type,
                "instance_number": instance_number,
            },
        )

        if response.get("success"):
            return response.get("value")
        else:
            logger.warning(
                f"Failed to read {object_type}:{instance_number} "
                f"from device {device_id}"
            )
            return None

    def read_device_points(self, device_id: int) -> dict:
        """
        Read all point values from a BACnet device

        Args:
            device_id: BACnet device ID

        Returns:
            Result dict with success status and readings count
        """
        response = self._make_request(
            "POST", f"/api/devices/{device_id}/read-all", timeout=120
        )

        return response

    def get_device_info(self, device_id: int, ip_address: str) -> dict:
        """
        Get device information

        Args:
            device_id: BACnet device ID
            ip_address: Device IP address

        Returns:
            Device info dict
        """
        response = self._make_request(
            "POST", f"/api/devices/{device_id}/info", data={"ip_address": ip_address}
        )

        if response.get("success"):
            return response.get("device", {})
        else:
            return {}


# Singleton instance
_client = None


def get_bacnet_api_client() -> BACnetAPIClient:
    """Get singleton BACnet API client instance"""
    global _client
    if _client is None:
        _client = BACnetAPIClient()
    return _client
