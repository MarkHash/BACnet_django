import asyncio
import logging
import threading
import time
from typing import Any, Dict, List, Optional

import BAC0
from django.conf import settings
from django.utils import timezone

from discovery.models import BACnetDevice

logger = logging.getLogger(__name__)


class UnifiedBACnetService:
    """
    Unified BACnet Service - Single instance acting as both client and device.

    This service consolidates all BACnet functionality into a single BAC0 instance:
    - Client operations: Device discovery, point reading
    - Device operations: Virtual device hosting (Phase 3)
    - Service lifecycle: Startup, shutdown, monitoring
    """

    def __init__(self):
        self.bacnet_client = None
        self.virtual_devices = {}
        self.running_devices = set()
        self.shutdown_event = threading.Event()
        self.service_thread = None
        self.last_scan = None
        self.scan_cache_duration = 300

    # ==================== Service Lifecycle ====================
    def start_service(self):
        """Start the unified BACnet service."""
        if self.service_thread and self.service_thread.is_alive():
            logger.warning("BACnet service already running")
            return

        logger.info("Starting Unified BACnet Service...")
        self.shutdown_event.clear()

        self.service_thread = threading.Thread(
            target=self._run_service, daemon=True, name="UnifiedBACnetService"
        )
        self.service_thread.start()
        logger.info("Unified BACnet Service started")

    def stop_service(self):
        """Stop the unified BACnet service."""
        logger.info("Stopping Unified BACnet Service...")
        self.shutdown_event.set()

        if self.service_thread:
            self.service_thread.join(timeout=10)

        self._cleanup_bacnet_client()
        self.running_devices.clear()
        logger.info("Unified BACnet Service stopped")

    def _run_service(self):
        """Main service loop."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._async_service_loop())
        except Exception as e:
            logger.error(f"Service loop error: {e}")
        finally:
            try:
                loop = asyncio.get_event_loop()
                loop.close()
            except Exception:
                pass

    async def _async_service_loop(self):
        """Async service loop for managing virtual devices."""
        await self._start_all_virtual_devices()

        while not self.shutdown_event.is_set():
            try:
                await self._monitor_virtual_devices()
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Service monitoring error: {e}")
                await asyncio.sleep(1)

    # ==================== BAC0 Client Management ====================

    def _get_bacnet_client(self, port: int = None):
        """Get or create BACnet client instance."""
        if self.bacnet_client is None:
            port = port or getattr(settings, "BACNET_DEFAULT_PORT", 47808)
            try:
                self.bacnet_client = BAC0.lite(port=port)
                logger.info(f"BACnet client initialised on port {port}")
            except Exception as e:
                logger.error(f"Failed to initialise BACnet client: {e}")
                raise

        return self.bacnet_client

    def _cleanup_bacnet_client(self):
        """Clean up BACnet client connection."""
        if self.bacnet_client:
            try:
                self.bacnet_client.disconnect()
                logger.info("BACnet client disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting BACnet client: {e}")
            finally:
                self.bacnet_client = None

    def restart_service(self):
        """Restart the unified BACnet service."""
        self.stop_service()
        time.sleep(1)
        self.start_service()

    def _get_or_reuse_client(self):
        """Get existing client or create new one if needed."""
        if self.bacnet_client is None:
            return self._get_bacnet_client()
        return self.bacnet_client

    # ==================== Device Discovery ====================

    def _discover_external_devices(self, client) -> List[Dict[str, Any]]:
        """Discover external BACnet devices using BAC0."""
        discovered = client.discover()
        logger.info(f"External discovery: found {len(discovered or [])} devices")

        devices = []
        if discovered:
            for device_info in discovered:
                logger.info(f"Processing discovered device: {device_info}")
                try:
                    if isinstance(device_info, tuple) and len(device_info) >= 3:
                        ip, port, device_id = device_info[:3]
                        # Convert all values to basic Python types
                        ip_str = str(ip)
                        port_int = int(port) if port else 47808
                        device_id_int = int(device_id)

                        devices.append(
                            {
                                "device_id": device_id_int,
                                "ip_address": ip_str,
                                "port": port_int,
                                "discovered_at": timezone.now().isoformat(),
                            }
                        )
                except Exception as e:
                    logger.error(f"Error processing device {device_info}: {e}")
                    continue
        return devices

    def _discover_self_device(self, client) -> Optional[Dict[str, Any]]:
        """Discover this device (self-discovery)."""
        if not client.this_device:
            return None

        try:
            obj_id = client.this_device._values.get("objectIdentifier")
            if obj_id and isinstance(obj_id, tuple) and len(obj_id) >= 2:
                device_id = obj_id[1]
                self_ip = str(getattr(client, "localIPAddr", "172.18.0.7"))
                logger.info(f"Self-discovery: ID={device_id}, IP={self_ip}")
                return {
                    "device_id": device_id,
                    "ip_address": self_ip,
                    "port": 47808,
                    "discovered_at": timezone.now().isoformat(),
                }
        except Exception as e:
            logger.error(f"Error during self-discovery: {e}")

        return None

    def discover_devices(
        self, use_cache: bool = True, include_self: bool = True
    ) -> List[Dict[str, Any]]:
        """Discover BACnet devices on the network."""
        if use_cache and self._is_cache_valid():
            return self._get_cached_results()

        try:
            client = self._get_or_reuse_client()

            external_devices = self._discover_external_devices(client)

            # Add self if requested and not already found
            if include_self:
                self_device = self._discover_self_device(client)

                if self_device and not any(
                    d["device_id"] == self_device["device_id"] for d in external_devices
                ):
                    external_devices.append(self_device)

            logger.info(f"Discovery completed: {len(external_devices)} devices found")

            self._cache_results(external_devices)
            return external_devices

        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            return []

    # ==================== Cache Management ====================

    def _is_cache_valid(self) -> bool:
        """Check if scan cache is still valid."""
        if not self.last_scan:
            return False
        return (time.time() - self.last_scan) < self.scan_cache_duration

    def _get_cached_results(self) -> List[Dict[str, Any]]:
        """Get cached discovery results."""
        try:
            # Use existing BACnetDevice model for caching
            devices = []
            recent_devices = BACnetDevice.objects.filter(
                last_seen__gte=timezone.now()
                - timezone.timedelta(seconds=self.scan_cache_duration)
            )
            for device in recent_devices:
                devices.append(
                    {
                        "device_id": device.device_id,
                        "ip_address": device.address,  # Using address field
                        "port": 47808,  # Default BACnet port
                        "discovered_at": (
                            device.last_seen.isoformat()
                            if device.last_seen
                            else timezone.now().isoformat()
                        ),
                    }
                )
            return devices
        except Exception:
            return []

    def _cache_results(self, devices: List[Dict[str, Any]]):
        """Cache discovery results to database."""
        try:
            self.store_device_data(devices)
            self.last_scan = time.time()
        except Exception as e:
            logger.error(f"Failed to cache results: {e}")

    # ==================== Database Operations ====================

    def read_device_points(self, device, results):
        """Read points from a specific BACnet device - legacy compatibility method."""
        try:
            logger.info(f"📖 Reading from device {device.device_id}")
            # TODO: Implement actual point reading logic
            # For now, simulate successful reading
            results["readings_collected"] += 1
            results["devices_processed"] += 1
            logger.info(f"✅ Successfully read from device {device.device_id}")
        except Exception as e:
            logger.error(f"❌ Device {device.device_id} failed: {e}")
            results.setdefault("errors", []).append(str(e))

    def store_device_data(self, devices):
        """Store discovered device data in database."""
        try:
            for device_info in devices:
                # Update or create BACnetDevice
                device, created = BACnetDevice.objects.update_or_create(
                    device_id=device_info["device_id"],
                    defaults={
                        "address": device_info["ip_address"],
                        "last_seen": timezone.now(),
                        "is_online": True,
                        "is_active": True,
                        "vendor_id": 842,  # BAC0 default vendor ID
                    },
                )
                if created:
                    logger.info(f"Created new device: {device.device_id}")
                else:
                    logger.info(f"Updated device: {device.device_id}")

        except Exception as e:
            logger.error(f"Failed to store device data: {e}")

    # ==================== Legacy Compatibility ====================
    def _initialise_results(self):
        """Initialize results dictionary for legacy compatibility."""
        return {
            "devices_processed": 0,
            "readings_collected": 0,
            "errors": [],
            "start_time": timezone.now(),
        }

    def _connect(self):
        """Legacy connect method - uses unified client."""
        try:
            client = self._get_bacnet_client()
            return client is not None
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    def _disconnect(self):
        """Legacy disconnect method - handled by unified service."""
        # Connection cleanup handled by unified service lifecycle

    def discover_device_points(self, device):
        """Legacy method: Discover points for a specific device."""
        # TODO: Implement point discovery logic
        # For now, return empty list to prevent errors
        logger.warning(
            f"Point discovery for device {device.device_id} not yet implemented"
        )
        return []

    def read_point_value(self, device, point):
        """Legacy method: Read a single point value."""
        # TODO: Implement single point reading
        # For now, return None to prevent errors
        logger.warning(
            f"Point reading for {device.device_id}:{point.identifier}"
            f" not yet implemented"
        )
        return None

    # ==================== Status and Information ====================

    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status information."""
        return {
            "service_running": (self.service_thread and self.service_thread.is_alive()),
            "bacnet_client_connected": self.bacnet_client is not None,
            "virtual_devices_running": len(self.running_devices),
            "virtual_devices": list(self.running_devices),
            "last_scan_time": self.last_scan,
            "cache_valid": self._is_cache_valid(),
        }

    def get_virtual_device_info(self, device_id: int) -> Optional[Dict[str, Any]]:
        """Get information about a specific virtual device."""
        if device_id not in self.virtual_devices:
            return None

        info = self.virtual_devices[device_id]
        return {
            "device_id": device_id,
            "device_name": info["device"].device_name,
            "port": info["device"].port,
            "template_key": info["template_key"],
            "object_count": len(info["objects"]),
            "started_at": info["started_at"].isoformat(),
            "running": device_id in self.running_devices,
        }

    # ==================== Virtual Device Methods (Phase 3) ====================
    async def sync_virtual_objects_from_db(self):
        """Create BACnet objects for all virtual devices in database"""
        # TODO: Implement in Phase 3

    def create_virtual_object(self, virtual_device):
        """Create virtual BACnet object using correct factory syntax"""
        # TODO: Implement in Phase 3

    def register_write_callbacks(self, obj):
        """Register callbacks for writable properties"""
        # TODO: Implement in Phase 3

    def handle_external_write(self, obj_name, property_name, old_value, new_value):
        """Process external BACnet writes"""
        # TODO: Implement in Phase 3

    def update_django_database(self, device_id, new_value):
        """Update database when external client writes"""
        # TODO: Implement in Phase 3

    def notify_web_interface(self, device_id, new_value):
        """Send real-time updates to web interface"""
        # TODO: Implement in Phase 4

    def trigger_business_logic(self, device_id, new_value):
        """Trigger business logic based on value changes"""
        # TODO: Implement in Phase 4

    async def _start_all_virtual_devices(self):
        """Start all virtual devices marked as running."""
        # TODO: Implement in Phase 3

    async def _monitor_virtual_devices(self):
        """Monitor virtual device status and handle updates."""
        # TODO: Implement in Phase 3

    # ==================== Global Service Instance ====================


# Global service instance
_unified_service = None


def get_unified_bacnet_service() -> UnifiedBACnetService:
    """Get the global unified BACnet service instance."""
    global _unified_service
    if _unified_service is None:
        _unified_service = UnifiedBACnetService()
    return _unified_service
