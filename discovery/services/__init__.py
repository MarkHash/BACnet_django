"""
Discovery Services Package

This package contains service classes for BACnet operations:
- UnifiedBACnetService: Main service for BACnet discovery and virtual devices
- Object templates: BACnet object configurations for virtual devices
"""

from .unified_bacnet_service import UnifiedBACnetService, get_unified_bacnet_service

__all__ = ["UnifiedBACnetService", "get_unified_bacnet_service"]
