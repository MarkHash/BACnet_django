import atexit

from django.apps import AppConfig


class DiscoveryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "discovery"

    def ready(self):
        """Initialize unified BACnet service when Django starts."""
        try:
            from .services.unified_bacnet_service import get_unified_bacnet_service

            if not hasattr(self, "_bacnet_service_started"):
                self.bacnet_service = get_unified_bacnet_service()
                self.bacnet_service.start_service()
                self._bacnet_service_started = True

                # Register cleanup on Django shutdown
                atexit.register(self.cleanup_bacnet_service)
        except ImportError:
            # Handle case where unified service isn't available yet
            pass

    def cleanup_bacnet_service(self):
        """Clean up BACnet service on shutdown."""
        if hasattr(self, "bacnet_service"):
            self.bacnet_service.stop_service()
