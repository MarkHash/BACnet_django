from django.apps import AppConfig


class DiscoveryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "discovery"

    def ready(self):
        """Initialize BACnet API service when Django starts."""
        try:
            from .services.api_bacnet_service import get_api_bacnet_service

            if not hasattr(self, "_bacnet_service_initialized"):
                # Initialize API-based service (no background thread needed)
                self.bacnet_service = get_api_bacnet_service()
                self._bacnet_service_initialized = True

                # Log service initialization
                import logging

                logger = logging.getLogger(__name__)
                logger.info("BACnet API service initialized (uses HTTP API client)")

        except ImportError as e:
            # Handle case where service isn't available yet
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"BACnet API service not available: {e}")
