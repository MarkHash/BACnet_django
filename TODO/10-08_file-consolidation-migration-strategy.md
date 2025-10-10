# File Consolidation & Migration Strategy
**Date:** October 8, 2025
**Branch:** feat/unified-bacnet-service
**Goal:** Consolidate 14 files into 9 files with unified BACnet service architecture

## Current vs Target File Structure

### **Current Structure (14 main files):**
```
discovery/
├── models.py                          # 8KB - Django models
├── views.py                          # 19KB - Web views + some API logic
├── api_views.py                      # 10KB - API endpoints
├── services.py                       # 23KB - BACnet discovery service
├── virtual_device_service.py         # 4KB - Virtual device management
├── forms.py                          # 2KB - Django forms
├── serializers.py                    # 1KB - DRF serializers
├── urls.py                           # 2KB - URL routing
├── admin.py                          # 2KB - Django admin
├── constants.py                      # 2KB - Constants
├── decorators.py                     # 2KB - Custom decorators
├── exceptions.py                     # 4KB - Custom exceptions
├── apps.py                           # 0.2KB - App configuration
└── management/commands/
    └── run_virtual_devices.py       # 3KB - Virtual device runner

Total: ~82KB across 14 files
```

### **Target Structure (9 main files - 36% reduction):**
```
discovery/
├── models.py                         # 8KB - Django models (unchanged)
├── views.py                         # 12KB - Web views only (simplified)
├── api_views.py                     # 7KB - API endpoints (simplified)
├── services/
│   └── unified_bacnet_service.py    # 15KB - ALL BACnet functionality
├── forms.py                         # 2KB - Django forms (unchanged)
├── serializers.py                   # 1KB - DRF serializers (unchanged)
├── urls.py                          # 2KB - URL routing (unchanged)
├── admin.py                         # 2KB - Django admin (unchanged)
├── constants.py                     # 2KB - Constants (unchanged)
├── exceptions.py                    # 4KB - Custom exceptions (unchanged)
└── apps.py                          # 0.5KB - Enhanced for service startup

Total: ~55KB across 9 files (33% reduction)

REMOVED FILES:
❌ virtual_device_service.py          # Merged into unified service
❌ services.py                        # Replaced by unified service
❌ decorators.py                      # Potentially unused
❌ management/commands/run_virtual_devices.py  # No longer needed
```

## Migration Strategy: 3-Phase Approach

### **Phase 1: Create Unified Service (Parallel Implementation)**
**Goal:** Create new unified service while keeping existing code working
**Time:** Day 1 (4-6 hours)
**Risk:** Low (no existing code changes)

#### Step 1.1: Create Services Directory
```bash
mkdir -p discovery/services
touch discovery/services/__init__.py
```

#### Step 1.2: Create Unified Service
**File:** `discovery/services/unified_bacnet_service.py`

```python
"""
Unified BACnet Service - Consolidates all BACnet functionality

Replaces:
- discovery/services.py (BACnet discovery)
- discovery/virtual_device_service.py (Virtual device management)
- management/commands/run_virtual_devices.py (Virtual device runner)
"""

import logging
import time
from django.utils import timezone

import BAC0
from BAC0.core.devices.local.models import (
    analog_input, analog_output, binary_input, binary_output
)

from ..models import VirtualBACnetDevice, BACnetDevice, BACnetReading
from ..exceptions import BACnetConnectionError

logger = logging.getLogger(__name__)

class UnifiedBACnetService:
    """Single service handling all BACnet operations"""

    def __init__(self):
        self.bacnet = None
        self.virtual_objects = {}
        self.is_running = False
        self.device_id = 8888
        self.device_name = "Django_BMS"
        self.port = 47808

    # =============================================================================
    # SERVICE LIFECYCLE
    # =============================================================================

    def start_service(self):
        """Start unified BACnet service"""
        try:
            logger.info("🚀 Starting Unified BACnet Service...")

            self.bacnet = BAC0.lite(
                deviceId=self.device_id,
                localObjName=self.device_name,
                port=self.port
            )

            self.is_running = True
            self.sync_virtual_objects_from_db()

            logger.info(f"✅ Django_BMS device {self.device_id} ready on port {self.port}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to start service: {e}")
            raise BACnetConnectionError(f"Service startup failed: {e}")

    def stop_service(self):
        """Stop unified BACnet service"""
        try:
            if self.bacnet:
                self.bacnet.disconnect()
                self.bacnet = None

            self.is_running = False
            self.virtual_objects.clear()
            logger.info("✅ Unified BACnet service stopped")

        except Exception as e:
            logger.error(f"❌ Error stopping service: {e}")

    # =============================================================================
    # CLIENT BEHAVIOR - Replaces discovery/services.py functionality
    # =============================================================================

    def discover_real_devices(self):
        """Discover real BACnet devices (replaces BACnetService.discover_devices)"""
        if not self.is_running:
            raise BACnetConnectionError("Service not running")

        try:
            logger.info("🔍 Discovering real BACnet devices...")
            devices = self.bacnet.discover()

            if devices:
                self.store_real_device_data(devices)
                logger.info(f"📡 Found {len(devices)} real devices")

            return devices or []

        except Exception as e:
            logger.error(f"❌ Discovery failed: {e}")
            raise BACnetConnectionError(f"Discovery failed: {e}")

    def read_device_points(self, device_id, timeout=10):
        """Read points from real device (replaces BACnetService.discover_points)"""
        try:
            device = BACnetDevice.objects.get(device_id=device_id)
            device_address = device.address

            # Use existing point discovery logic from services.py
            logger.info(f"📖 Reading points for device {device_id} at {device_address}")

            # TODO: Port existing point discovery logic here
            points = []  # Placeholder

            return points

        except BACnetDevice.DoesNotExist:
            raise BACnetConnectionError(f"Device {device_id} not found")
        except Exception as e:
            logger.error(f"❌ Failed to read points: {e}")
            raise BACnetConnectionError(f"Point reading failed: {e}")

    def store_real_device_data(self, devices):
        """Store discovered devices in database"""
        for device_info in devices:
            if len(device_info) >= 3 and device_info[2] != self.device_id:
                device_id = device_info[2]
                address = f"{device_info[0]}:{device_info[1]}"
                vendor_id = device_info[3] if len(device_info) > 3 else 0

                device, created = BACnetDevice.objects.get_or_create(
                    device_id=device_id,
                    defaults={
                        'address': address,
                        'vendor_id': vendor_id,
                        'is_online': True,
                        'last_seen': timezone.now()
                    }
                )

                if not created:
                    device.is_online = True
                    device.last_seen = timezone.now()
                    device.save()

    # =============================================================================
    # DEVICE BEHAVIOR - Replaces virtual_device_service.py functionality
    # =============================================================================

    def create_virtual_device(self, device_id, device_name, description=""):
        """Create virtual device (replaces VirtualDeviceService.create_virtual_device)"""
        try:
            # Create in database
            virtual_device = VirtualBACnetDevice.objects.create(
                device_id=device_id,
                device_name=device_name,
                description=description,
                port=self.port,
                is_running=True
            )

            # Create BACnet objects immediately
            self.create_virtual_objects_for_device(virtual_device)

            logger.info(f"✅ Created virtual device {device_id}: {device_name}")
            return virtual_device

        except Exception as e:
            logger.error(f"❌ Failed to create virtual device: {e}")
            raise

    def delete_virtual_device(self, device_id):
        """Delete virtual device (replaces VirtualDeviceService.delete_virtual_device)"""
        try:
            virtual_device = VirtualBACnetDevice.objects.get(device_id=device_id)

            # Remove BACnet objects
            self.remove_virtual_objects_for_device(device_id)

            # Remove from database
            virtual_device.delete()

            logger.info(f"✅ Deleted virtual device {device_id}")
            return True

        except VirtualBACnetDevice.DoesNotExist:
            logger.warning(f"Virtual device {device_id} not found")
            return False

    def sync_virtual_objects_from_db(self):
        """Create BACnet objects for all virtual devices in database"""
        virtual_devices = VirtualBACnetDevice.objects.filter(is_running=True)

        for virtual_device in virtual_devices:
            self.create_virtual_objects_for_device(virtual_device)

        logger.info(f"✅ Synced {virtual_devices.count()} virtual devices")

    def create_virtual_objects_for_device(self, virtual_device):
        """Create BACnet objects based on device type"""
        device_id = virtual_device.device_id
        device_name = virtual_device.device_name.lower()
        objects_created = []

        try:
            if "temperature" in device_name or "sensor" in device_name:
                # Temperature sensor: analog inputs
                temp_obj = analog_input(
                    name=f"Virtual_{device_id}_Temperature",
                    description=f"{virtual_device.device_name} Temperature",
                    presentValue=72.5,
                    properties={"units": "degreesCelsius"}
                )
                temp_obj.add_objects_to_application(self.bacnet)
                objects_created.append("Temperature")

                humidity_obj = analog_input(
                    name=f"Virtual_{device_id}_Humidity",
                    description=f"{virtual_device.device_name} Humidity",
                    presentValue=45.0,
                    properties={"units": "percent"}
                )
                humidity_obj.add_objects_to_application(self.bacnet)
                objects_created.append("Humidity")

            elif "hvac" in device_name or "controller" in device_name:
                # HVAC controller: writable outputs
                setpoint_obj = analog_output(
                    name=f"Virtual_{device_id}_Setpoint",
                    description=f"{virtual_device.device_name} Setpoint",
                    presentValue=70.0,
                    properties={
                        "units": "degreesCelsius",
                        "relinquishDefault": 70.0,
                        "priorityArray": [None] * 16
                    }
                )
                setpoint_obj.add_objects_to_application(self.bacnet)
                objects_created.append("Setpoint")

                fan_obj = binary_output(
                    name=f"Virtual_{device_id}_Fan",
                    description=f"{virtual_device.device_name} Fan",
                    presentValue=False,
                    properties={
                        "activeText": "On",
                        "inactiveText": "Off",
                        "relinquishDefault": False,
                        "priorityArray": [None] * 16
                    }
                )
                fan_obj.add_objects_to_application(self.bacnet)
                objects_created.append("Fan")

            elif "light" in device_name:
                # Lighting controller: binary and analog outputs
                light_obj = binary_output(
                    name=f"Virtual_{device_id}_Lights",
                    description=f"{virtual_device.device_name} Lights",
                    presentValue=False,
                    properties={
                        "activeText": "On",
                        "inactiveText": "Off",
                        "relinquishDefault": False,
                        "priorityArray": [None] * 16
                    }
                )
                light_obj.add_objects_to_application(self.bacnet)
                objects_created.append("Lights")

                dimmer_obj = analog_output(
                    name=f"Virtual_{device_id}_Dimmer",
                    description=f"{virtual_device.device_name} Dimmer",
                    presentValue=75.0,
                    properties={
                        "units": "percent",
                        "relinquishDefault": 0.0,
                        "priorityArray": [None] * 16
                    }
                )
                dimmer_obj.add_objects_to_application(self.bacnet)
                objects_created.append("Dimmer")

            else:
                # Default: status input
                status_obj = analog_input(
                    name=f"Virtual_{device_id}_Status",
                    description=f"{virtual_device.device_name} Status",
                    presentValue=100.0,
                    properties={"units": "percent"}
                )
                status_obj.add_objects_to_application(self.bacnet)
                objects_created.append("Status")

            self.virtual_objects[device_id] = objects_created
            logger.info(f"✅ Created objects for device {device_id}: {', '.join(objects_created)}")

        except Exception as e:
            logger.error(f"❌ Error creating objects for device {device_id}: {e}")

    def remove_virtual_objects_for_device(self, device_id):
        """Remove BACnet objects for device"""
        if device_id in self.virtual_objects:
            # TODO: Implement object removal from BAC0 application
            del self.virtual_objects[device_id]
            logger.info(f"✅ Removed objects for device {device_id}")

    # =============================================================================
    # UTILITY METHODS
    # =============================================================================

    def get_service_status(self):
        """Get current service status"""
        return {
            'is_running': self.is_running,
            'device_id': self.device_id,
            'device_name': self.device_name,
            'port': self.port,
            'virtual_objects_count': len(self.virtual_objects),
            'virtual_devices': list(self.virtual_objects.keys())
        }

# Global service instance
_unified_service = None

def get_unified_service():
    """Get global unified service instance"""
    global _unified_service
    if _unified_service is None:
        _unified_service = UnifiedBACnetService()
    return _unified_service

def start_unified_service():
    """Start the global unified service"""
    service = get_unified_service()
    if not service.is_running:
        service.start_service()
    return service

def stop_unified_service():
    """Stop the global unified service"""
    global _unified_service
    if _unified_service and _unified_service.is_running:
        _unified_service.stop_service()
        _unified_service = None
```

#### Step 1.3: Update Services Init File
**File:** `discovery/services/__init__.py`

```python
"""
BACnet Services

Unified BACnet service that replaces:
- discovery.services.BACnetService
- discovery.virtual_device_service.VirtualDeviceService
- management.commands.run_virtual_devices
"""

from .unified_bacnet_service import (
    UnifiedBACnetService,
    get_unified_service,
    start_unified_service,
    stop_unified_service
)

__all__ = [
    'UnifiedBACnetService',
    'get_unified_service',
    'start_unified_service',
    'stop_unified_service'
]
```

#### Step 1.4: Update Django App Configuration
**File:** `discovery/apps.py`

```python
from django.apps import AppConfig
import atexit
import logging

logger = logging.getLogger(__name__)

class DiscoveryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'discovery'

    def ready(self):
        """Start unified BACnet service when Django starts"""
        # Only start service once and avoid during migrations
        if not getattr(self, '_service_started', False):
            try:
                from .services import start_unified_service

                # Start the unified service
                service = start_unified_service()
                self.bacnet_service = service
                self._service_started = True

                # Register cleanup on Django shutdown
                atexit.register(self.cleanup_bacnet_service)

                logger.info("✅ Unified BACnet service started with Django")

            except Exception as e:
                logger.error(f"❌ Failed to start unified BACnet service: {e}")
                # Don't crash Django if BACnet service fails
                pass

    def cleanup_bacnet_service(self):
        """Clean up BACnet service on Django shutdown"""
        try:
            if hasattr(self, 'bacnet_service'):
                self.bacnet_service.stop_service()
                logger.info("✅ Unified BACnet service stopped")
        except Exception as e:
            logger.error(f"❌ Error stopping BACnet service: {e}")
```

### **Phase 2: Update Views to Use Unified Service (Gradual Migration)**
**Goal:** Update all views to use unified service while keeping old services as backup
**Time:** Day 2 (4-6 hours)
**Risk:** Medium (changes existing functionality)

#### Step 2.1: Update Web Views
**File:** `discovery/views.py` (Key changes)

```python
# OLD imports (to be removed in Phase 3)
# from .services import BACnetService
# from .virtual_device_service import VirtualDeviceService

# NEW import
from django.apps import apps

def start_discovery(request):
    """Start device discovery using unified service"""
    try:
        # Get unified service from Django app
        discovery_app = apps.get_app_config('discovery')
        service = discovery_app.bacnet_service

        # Use unified service for discovery
        devices = service.discover_real_devices()

        return JsonResponse({
            'success': True,
            'message': f'Discovery completed. Found {len(devices)} devices.',
            'devices': [{'deviceId': d[2], 'address': d[0]} for d in devices]
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Discovery failed: {str(e)}'
        })

def discover_points(request, device_id):
    """Discover points using unified service"""
    try:
        discovery_app = apps.get_app_config('discovery')
        service = discovery_app.bacnet_service

        points = service.read_device_points(device_id)

        return JsonResponse({
            'success': True,
            'message': f'Found {len(points)} points for device {device_id}',
            'points': points
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Point discovery failed: {str(e)}'
        })

def create_virtual_device(request):
    """Create virtual device using unified service"""
    if request.method == 'POST':
        form = VirtualDeviceCreateForm(request.POST)
        if form.is_valid():
            try:
                # Use unified service to create virtual device
                discovery_app = apps.get_app_config('discovery')
                service = discovery_app.bacnet_service

                virtual_device = service.create_virtual_device(
                    device_id=form.cleaned_data['device_id'],
                    device_name=form.cleaned_data['device_name'],
                    description=form.cleaned_data['description']
                )

                messages.success(request, f'Virtual device {virtual_device.device_id} created successfully!')
                return redirect('discovery:virtual_device_list')

            except Exception as e:
                messages.error(request, f'Failed to create virtual device: {str(e)}')
    else:
        form = VirtualDeviceCreateForm()

    return render(request, 'discovery/virtual_device_create.html', {'form': form})

def delete_virtual_device(request, device_id):
    """Delete virtual device using unified service"""
    try:
        discovery_app = apps.get_app_config('discovery')
        service = discovery_app.bacnet_service

        success = service.delete_virtual_device(device_id)

        if success:
            return JsonResponse({'success': True, 'message': 'Device deleted successfully'})
        else:
            return JsonResponse({'success': False, 'message': 'Device not found'})

    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Delete failed: {str(e)}'})
```

#### Step 2.2: Update API Views
**File:** `discovery/api_views.py` (Key changes)

```python
from django.apps import apps
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['POST'])
def api_start_discovery(request):
    """API endpoint for device discovery"""
    try:
        discovery_app = apps.get_app_config('discovery')
        service = discovery_app.bacnet_service

        devices = service.discover_real_devices()

        return Response({
            'success': True,
            'devices_found': len(devices),
            'devices': [{'device_id': d[2], 'address': f"{d[0]}:{d[1]}"} for d in devices]
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
def api_service_status(request):
    """Get unified service status"""
    try:
        discovery_app = apps.get_app_config('discovery')
        service = discovery_app.bacnet_service

        status = service.get_service_status()

        return Response({
            'success': True,
            'service_status': status
        })

    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)
```

### **Phase 3: Remove Redundant Files (Clean Up)**
**Goal:** Remove old files and clean up codebase
**Time:** Day 3 (2-3 hours)
**Risk:** Low (everything should be working from unified service)

#### Step 3.1: Remove Virtual Device Service
```bash
# Backup first
cp discovery/virtual_device_service.py discovery/virtual_device_service.py.backup

# Remove the file
rm discovery/virtual_device_service.py

# Remove from git
git rm discovery/virtual_device_service.py
```

#### Step 3.2: Remove Management Command
```bash
# Backup first
cp discovery/management/commands/run_virtual_devices.py discovery/management/commands/run_virtual_devices.py.backup

# Remove the file
rm discovery/management/commands/run_virtual_devices.py

# Remove from git
git rm discovery/management/commands/run_virtual_devices.py
```

#### Step 3.3: Replace Original Services File
```bash
# Backup original services.py
cp discovery/services.py discovery/services.py.backup

# Create minimal compatibility wrapper
cat > discovery/services.py << 'EOF'
"""
Legacy BACnet Services (Compatibility Layer)

This file provides backward compatibility for any remaining code
that imports from discovery.services directly.

All functionality has been moved to discovery.services.unified_bacnet_service
"""

import warnings
from .services.unified_bacnet_service import get_unified_service

# Legacy compatibility - deprecated
class BACnetService:
    """Legacy BACnet service - use UnifiedBACnetService instead"""

    def __init__(self):
        warnings.warn(
            "BACnetService is deprecated. Use get_unified_service() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self._service = get_unified_service()

    def discover_devices(self, **kwargs):
        """Legacy method - redirects to unified service"""
        return self._service.discover_real_devices()

    def discover_points(self, device_id, **kwargs):
        """Legacy method - redirects to unified service"""
        return self._service.read_device_points(device_id)

# Maintain backward compatibility
def get_bacnet_service():
    """Legacy function - use get_unified_service() instead"""
    warnings.warn(
        "get_bacnet_service() is deprecated. Use get_unified_service() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return BACnetService()
EOF
```

#### Step 3.4: Clean Up Imports Throughout Codebase
```bash
# Find all files that import old services
grep -r "from.*services import" discovery/ --include="*.py"
grep -r "from.*virtual_device_service" discovery/ --include="*.py"

# Update imports manually:
# OLD: from .services import BACnetService
# NEW: from django.apps import apps; service = apps.get_app_config('discovery').bacnet_service

# OLD: from .virtual_device_service import VirtualDeviceService
# NEW: from django.apps import apps; service = apps.get_app_config('discovery').bacnet_service
```

#### Step 3.5: Remove Unused Decorators (If Applicable)
```bash
# Check if decorators.py is still used
grep -r "from.*decorators" discovery/ --include="*.py"

# If not used, remove it
# cp discovery/decorators.py discovery/decorators.py.backup
# rm discovery/decorators.py
# git rm discovery/decorators.py
```

## Testing Strategy

### **Phase 1 Testing: Parallel System**
```python
# Test unified service alongside existing system
def test_unified_service_parallel():
    # 1. Start unified service
    from discovery.services import start_unified_service
    service = start_unified_service()

    # 2. Test discovery
    devices = service.discover_real_devices()
    assert isinstance(devices, list)

    # 3. Test virtual device creation
    virtual_device = service.create_virtual_device(
        device_id=9999,
        device_name="Test Device"
    )
    assert virtual_device.device_id == 9999

    # 4. Test service status
    status = service.get_service_status()
    assert status['is_running'] == True

    # 5. Clean up
    service.delete_virtual_device(9999)
    service.stop_service()
```

### **Phase 2 Testing: View Integration**
```python
# Test updated views work with unified service
def test_views_with_unified_service():
    # 1. Test discovery endpoint
    response = client.post('/api/start-discovery/')
    assert response.status_code == 200

    # 2. Test virtual device creation
    response = client.post('/virtual-devices/create/', {
        'device_id': 8888,
        'device_name': 'Test Device'
    })
    assert response.status_code == 302  # Redirect after creation

    # 3. Test virtual device deletion
    response = client.post('/api/virtual-devices/8888/delete/')
    assert response.json()['success'] == True
```

### **Phase 3 Testing: Clean System**
```python
# Test system works after file removal
def test_consolidated_system():
    # 1. Verify old imports fail gracefully
    with pytest.warns(DeprecationWarning):
        from discovery.services import BACnetService

    # 2. Verify unified service works
    from discovery.services import get_unified_service
    service = get_unified_service()
    assert service.is_running

    # 3. Verify all endpoints work
    # ... test all web and API endpoints
```

## Rollback Plan

### **If Issues Occur During Migration:**

#### **Phase 1 Rollback (Easy):**
```bash
# Simply don't use unified service - old system still works
# Remove unified service directory if needed
rm -rf discovery/services/
```

#### **Phase 2 Rollback (Medium):**
```bash
# Restore original view files from git
git checkout HEAD~1 -- discovery/views.py
git checkout HEAD~1 -- discovery/api_views.py
git checkout HEAD~1 -- discovery/apps.py
```

#### **Phase 3 Rollback (Hard but possible):**
```bash
# Restore all removed files
cp discovery/virtual_device_service.py.backup discovery/virtual_device_service.py
cp discovery/services.py.backup discovery/services.py
cp discovery/management/commands/run_virtual_devices.py.backup discovery/management/commands/run_virtual_devices.py

# Restore to previous commit
git checkout HEAD~5 -- discovery/
```

## Success Metrics

### **Technical Metrics:**
1. ✅ **File Count Reduction**: 14 → 9 files (36% reduction)
2. ✅ **Code Size Reduction**: ~82KB → ~55KB (33% reduction)
3. ✅ **Single BACnet Instance**: Only one BAC0 connection
4. ✅ **All Functionality Works**: Discovery, virtual devices, web interface
5. ✅ **No Performance Regression**: Same or better response times
6. ✅ **Clean Architecture**: Single responsibility per remaining file

### **Business Metrics:**
1. ✅ **Maintainability**: Easier to understand and modify
2. ✅ **Testability**: Single service to test instead of multiple
3. ✅ **Scalability**: Better resource usage with unified service
4. ✅ **Documentation**: Clearer code organization and documentation

## Timeline Summary

**Total Migration Time: 10-15 hours over 3 days**

- **Day 1 (4-6 hours)**: Create unified service (safe, parallel)
- **Day 2 (4-6 hours)**: Update views to use unified service
- **Day 3 (2-3 hours)**: Remove old files and clean up

**Risk Level: Low to Medium**
- Phase 1: Very low risk (no existing code changes)
- Phase 2: Medium risk (view changes, but can rollback easily)
- Phase 3: Low risk (just cleanup, functionality already working)

**Outcome: Professional, maintainable, consolidated BACnet architecture** 🚀