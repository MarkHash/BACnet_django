# BACnet API Service Architecture - Implementation Plan

**Date:** October 13, 2025
**Branch:** feat/simplified-bacnet-core
**Goal:** Separate BACnet operations into standalone API service for clean architecture

---

## 🎯 Project Overview

### Current Architecture (Problems)
```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ HTTP
┌──────▼──────────────────────┐
│  Django (Docker/Local)      │
│  - UI + BACnet operations   │ ❌ Tightly coupled
│  - Network access issues    │ ❌ Docker networking problems
│  - Platform-specific setup  │ ❌ Inconsistent across Mac/Windows
└──────┬──────────────────────┘
       │
┌──────▼──────┐
│  PostgreSQL │
└─────────────┘
```

### Proposed Architecture (Clean Separation)
```
┌─────────────────────────────────────────────────────────────┐
│                         Browser (UI)                        │
└───────────────────────────────┬─────────────────────────────┘
                                │ HTTP
┌───────────────────────────────▼─────────────────────────────┐
│              Django Web Service (Docker)                    │
│              - Pure UI/API layer                            │
│              - No hardware dependencies                     │
│              - Platform agnostic                            │
└─────────────────────┬──────────────────┬────────────────────┘
                      │                  │
                      │ HTTP API         │ Database
                      │                  │
    ┌─────────────────▼──────┐    ┌──────▼─────────┐
    │  BACnet API Service    │    │  PostgreSQL    │
    │  (Windows/Mac Host)    │    │  (Docker)      │
    │  - Device discovery    │    │                │
    │  - Point reading       │    └────────────────┘
    │  - Virtual devices     │
    │  - Network access      │
    └────────────────────────┘
```

---

## 📋 Architecture Benefits

### Clean Separation of Concerns
- **Django Web**: Pure UI/API layer - no hardware dependencies
- **BACnet Service**: All BACnet operations in one place
- **Database**: Pure data storage

### Cross-Platform Consistency
- **Mac & Windows**: Identical setup (docker-compose + local BACnet service)
- **Linux**: Can run everything in Docker with `network_mode: host`

### Scalability & Maintainability
- Web and BACnet services can scale independently
- Easy to mock BACnet service for testing
- Single source of truth for BACnet operations
- Can replace BACnet service without touching Django

### Professional Architecture
- Industry-standard microservices pattern
- Clear API contracts
- Easier to test and debug
- Better for portfolio/resume

---

## 🏗️ Implementation Plan

### Phase 1: BACnet API Service (4-5 hours)

#### Step 1.1: Create FastAPI Service (~2 hours)
**File:** `bacnet_api_service.py` (root directory)

**Why FastAPI?**
- Automatic OpenAPI/Swagger documentation
- Built-in async support (good for BACnet operations)
- Type hints and validation
- Faster than Flask for I/O-bound operations

**API Endpoints:**
```python
# Device Discovery & Reading
POST   /api/discover                    # Discover BACnet devices
GET    /api/devices                     # List discovered devices (cached)
POST   /api/devices/{device_id}/points  # Discover device points
POST   /api/devices/{device_id}/read    # Read all points
POST   /api/points/read                 # Read single point

# Virtual Device Management
GET    /api/virtual-devices             # List running virtual devices
POST   /api/virtual-devices             # Create + start virtual device
GET    /api/virtual-devices/{id}        # Get virtual device details
DELETE /api/virtual-devices/{id}        # Stop + delete virtual device
POST   /api/virtual-devices/sync        # Sync from database (background)

# Service Health
GET    /api/health                      # Health check
GET    /docs                            # Swagger API documentation
```

**Core Implementation:**
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import BAC0
import asyncio
import logging

app = FastAPI(
    title="BACnet API Service",
    description="BACnet operations API for Django web application",
    version="1.0.0"
)

# Global BAC0 instance
bacnet_instance = None
discovered_devices_cache = {}

class DiscoveryResponse(BaseModel):
    success: bool
    devices: List[Dict]
    count: int

class PointReadRequest(BaseModel):
    device_id: int
    ip_address: str
    object_type: str
    instance_number: int

class PointReadResponse(BaseModel):
    success: bool
    value: Optional[str]
    error: Optional[str]

@app.on_event("startup")
async def startup_event():
    """Initialize BAC0 on startup"""
    global bacnet_instance
    try:
        bacnet_instance = BAC0.lite()
        logging.info(f"✅ BAC0 started on {bacnet_instance.localIPAddr}")
    except Exception as e:
        logging.error(f"❌ Failed to start BAC0: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean shutdown of BAC0"""
    global bacnet_instance
    if bacnet_instance:
        bacnet_instance.disconnect()
        logging.info("✅ BAC0 disconnected")

@app.post("/api/discover", response_model=DiscoveryResponse)
async def discover_devices():
    """Discover BACnet devices on network"""
    try:
        devices = bacnet_instance.discover()

        # Convert to Django-compatible format
        device_list = []
        for device in devices:
            device_list.append({
                "device_id": device[2],  # device instance
                "ip_address": device[0],  # IP address
                "port": device[1],  # BACnet port
            })

        # Cache results
        global discovered_devices_cache
        discovered_devices_cache = {d['device_id']: d for d in device_list}

        return DiscoveryResponse(
            success=True,
            devices=device_list,
            count=len(device_list)
        )
    except Exception as e:
        logging.error(f"Discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/devices/{device_id}/points")
async def discover_device_points(device_id: int):
    """Discover points for a specific device"""
    try:
        # Get device from cache or require IP
        if device_id not in discovered_devices_cache:
            raise HTTPException(status_code=404, detail="Device not found. Run discovery first.")

        device_info = discovered_devices_cache[device_id]
        device_address = f"{device_info['ip_address']}:{device_info['port']}"

        # Read object list
        object_list = bacnet_instance.read(f"{device_address} device {device_id} objectList")

        # Parse and return
        points = []
        for obj in object_list:
            obj_type, obj_instance = obj.split(':')
            points.append({
                "object_type": obj_type,
                "instance_number": int(obj_instance)
            })

        return {
            "success": True,
            "device_id": device_id,
            "points": points,
            "count": len(points)
        }
    except Exception as e:
        logging.error(f"Point discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/points/read", response_model=PointReadResponse)
async def read_point(request: PointReadRequest):
    """Read a single BACnet point value"""
    try:
        address = f"{request.ip_address} {request.object_type} {request.instance_number} presentValue"
        value = bacnet_instance.read(address)

        return PointReadResponse(
            success=True,
            value=str(value),
            error=None
        )
    except Exception as e:
        logging.error(f"Point read failed: {e}")
        return PointReadResponse(
            success=False,
            value=None,
            error=str(e)
        )

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "bacnet_connected": bacnet_instance is not None,
        "local_ip": str(bacnet_instance.localIPAddr) if bacnet_instance else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001, log_level="info")
```

#### Step 1.2: Add Virtual Device Management (~1-2 hours)
**Extend API with virtual device endpoints:**

```python
from discovery.models import VirtualBACnetDevice
import os
import django

# Setup Django for database access
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bacnet_project.settings")
django.setup()

# Track running virtual devices
running_virtual_devices = {}

class VirtualDeviceCreate(BaseModel):
    device_id: int
    device_name: str
    description: str = ""
    port: int = 47808

class VirtualDeviceResponse(BaseModel):
    device_id: int
    device_name: str
    description: str
    port: int
    is_running: bool
    created_at: str

@app.get("/api/virtual-devices")
async def list_virtual_devices():
    """List all running virtual devices"""
    try:
        devices = []
        for device_id, bacnet_device in running_virtual_devices.items():
            # Get from database
            db_device = VirtualBACnetDevice.objects.get(device_id=device_id)
            devices.append({
                "device_id": db_device.device_id,
                "device_name": db_device.device_name,
                "description": db_device.description,
                "port": db_device.port,
                "is_running": True,
                "local_ip": str(bacnet_device.localIPAddr)
            })

        return {
            "success": True,
            "devices": devices,
            "count": len(devices)
        }
    except Exception as e:
        logging.error(f"Failed to list virtual devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/virtual-devices", response_model=VirtualDeviceResponse)
async def create_virtual_device(request: VirtualDeviceCreate):
    """Create and start a new virtual BACnet device"""
    try:
        # Check if device ID already exists
        if VirtualBACnetDevice.objects.filter(device_id=request.device_id).exists():
            raise HTTPException(
                status_code=400,
                detail=f"Device ID {request.device_id} already exists"
            )

        # Check if port is in use
        if any(d.port == request.port for d in running_virtual_devices.values()):
            raise HTTPException(
                status_code=400,
                detail=f"Port {request.port} is already in use"
            )

        # Create in database
        device = VirtualBACnetDevice.objects.create(
            device_id=request.device_id,
            device_name=request.device_name,
            description=request.description,
            port=request.port,
            is_running=True
        )

        # Start virtual BACnet device
        bacnet_device = BAC0.lite(
            deviceId=device.device_id,
            port=device.port,
            localObjName=device.device_name
        )
        running_virtual_devices[device.device_id] = bacnet_device

        logging.info(f"✅ Virtual device {device.device_id} created and started on port {device.port}")

        return VirtualDeviceResponse(
            device_id=device.device_id,
            device_name=device.device_name,
            description=device.description,
            port=device.port,
            is_running=True,
            created_at=device.created_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to create virtual device: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/virtual-devices/{device_id}")
async def get_virtual_device(device_id: int):
    """Get details of a virtual device"""
    try:
        device = VirtualBACnetDevice.objects.get(device_id=device_id)
        is_running = device_id in running_virtual_devices

        response = {
            "device_id": device.device_id,
            "device_name": device.device_name,
            "description": device.description,
            "port": device.port,
            "is_running": is_running,
            "created_at": device.created_at.isoformat(),
            "updated_at": device.updated_at.isoformat()
        }

        if is_running:
            bacnet_device = running_virtual_devices[device_id]
            response["local_ip"] = str(bacnet_device.localIPAddr)

        return {"success": True, "device": response}
    except VirtualBACnetDevice.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    except Exception as e:
        logging.error(f"Failed to get virtual device: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/virtual-devices/{device_id}")
async def delete_virtual_device(device_id: int):
    """Stop and delete a virtual device"""
    try:
        # Stop if running
        if device_id in running_virtual_devices:
            running_virtual_devices[device_id].disconnect()
            del running_virtual_devices[device_id]
            logging.info(f"⏹️ Virtual device {device_id} stopped")

        # Delete from database
        device = VirtualBACnetDevice.objects.get(device_id=device_id)
        device.delete()

        logging.info(f"🗑️ Virtual device {device_id} deleted")

        return {
            "success": True,
            "message": f"Virtual device {device_id} stopped and deleted"
        }
    except VirtualBACnetDevice.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    except Exception as e:
        logging.error(f"Failed to delete virtual device: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/virtual-devices/sync")
async def sync_virtual_devices():
    """Sync virtual devices from Django database (background task)"""
    try:
        # Get devices marked as running from database
        devices_to_run = VirtualBACnetDevice.objects.filter(is_running=True)

        # Start new devices
        for device in devices_to_run:
            if device.device_id not in running_virtual_devices:
                try:
                    bacnet_device = BAC0.lite(
                        deviceId=device.device_id,
                        port=device.port,
                        localObjName=device.device_name
                    )
                    running_virtual_devices[device.device_id] = bacnet_device
                    logging.info(f"✅ Virtual device {device.device_id} started on port {device.port}")
                except Exception as e:
                    logging.error(f"❌ Failed to start virtual device {device.device_id}: {e}")

        # Stop removed devices
        current_device_ids = set(d.device_id for d in devices_to_run)
        for device_id in list(running_virtual_devices.keys()):
            if device_id not in current_device_ids:
                running_virtual_devices[device_id].disconnect()
                del running_virtual_devices[device_id]
                logging.info(f"⏹️ Virtual device {device_id} stopped")

        return {
            "success": True,
            "running_devices": len(running_virtual_devices),
            "device_ids": list(running_virtual_devices.keys())
        }
    except Exception as e:
        logging.error(f"Virtual device sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task to sync virtual devices every 10 seconds
@app.on_event("startup")
async def start_virtual_device_sync():
    """Start background sync loop"""
    asyncio.create_task(virtual_device_sync_loop())

async def virtual_device_sync_loop():
    """Background loop to sync virtual devices from database"""
    while True:
        try:
            await sync_virtual_devices()
        except Exception as e:
            logging.error(f"Virtual device sync error: {e}")
        await asyncio.sleep(10)

# ==================== Virtual Device Points ====================

from BAC0.core.devices.local.models import (
    analog_input, analog_output,
    binary_input, binary_output
)

class VirtualDevicePointCreate(BaseModel):
    object_type: str  # analogInput, analogOutput, binaryInput, binaryOutput
    instance_number: int
    object_name: str
    present_value: float
    description: str = ""
    units: str = "noUnits"
    active_text: str = "Active"
    inactive_text: str = "Inactive"

# Track points for each device
virtual_device_points = {}  # {device_id: [point_objects]}

@app.get("/api/virtual-devices/{device_id}/points")
async def list_virtual_device_points(device_id: int):
    """List all points in a virtual device"""
    try:
        if device_id not in running_virtual_devices:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not running")

        bacnet_device = running_virtual_devices[device_id]

        # Get object list from BAC0 device
        points = []
        if hasattr(bacnet_device, 'this_application') and hasattr(bacnet_device.this_application, 'objectList'):
            for obj in bacnet_device.this_application.objectList:
                if obj[0] != 'device':  # Skip device object
                    points.append({
                        "object_type": obj[0],
                        "instance_number": obj[1],
                    })

        return {
            "success": True,
            "device_id": device_id,
            "points": points,
            "count": len(points)
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to list points: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/virtual-devices/{device_id}/points")
async def add_virtual_device_point(device_id: int, request: VirtualDevicePointCreate):
    """Add a point/object to a virtual device"""
    try:
        if device_id not in running_virtual_devices:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not running")

        bacnet_device = running_virtual_devices[device_id]

        # Create appropriate point type
        point_obj = None

        if request.object_type == "analogInput":
            point_obj = analog_input(
                instance=request.instance_number,
                name=request.object_name,
                description=request.description,
                presentValue=request.present_value,
                units=request.units
            )
        elif request.object_type == "analogOutput":
            point_obj = analog_output(
                instance=request.instance_number,
                name=request.object_name,
                description=request.description,
                presentValue=request.present_value,
                units=request.units
            )
        elif request.object_type == "binaryInput":
            point_obj = binary_input(
                instance=request.instance_number,
                name=request.object_name,
                description=request.description,
                presentValue=int(request.present_value),
                activeText=request.active_text,
                inactiveText=request.inactive_text
            )
        elif request.object_type == "binaryOutput":
            point_obj = binary_output(
                instance=request.instance_number,
                name=request.object_name,
                description=request.description,
                presentValue=int(request.present_value),
                activeText=request.active_text,
                inactiveText=request.inactive_text
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported object type: {request.object_type}"
            )

        # Register point with device
        point_obj.add_objects_to_application(bacnet_device)

        # Track point
        if device_id not in virtual_device_points:
            virtual_device_points[device_id] = []
        virtual_device_points[device_id].append(point_obj)

        logging.info(f"✅ Added {request.object_type}:{request.instance_number} to device {device_id}")

        return {
            "success": True,
            "device_id": device_id,
            "point": {
                "object_type": request.object_type,
                "instance_number": request.instance_number,
                "object_name": request.object_name
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to add point: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/virtual-devices/{device_id}/points/{object_type}/{instance_number}")
async def remove_virtual_device_point(device_id: int, object_type: str, instance_number: int):
    """Remove a point from a virtual device"""
    try:
        if device_id not in running_virtual_devices:
            raise HTTPException(status_code=404, detail=f"Device {device_id} not running")

        # Note: BAC0 doesn't easily support removing objects
        # This is a limitation we should document
        raise HTTPException(
            status_code=501,
            detail="Point removal not currently supported. Restart device to clear points."
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to remove point: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### Step 1.3: Add Requirements (~15 min)
**File:** `requirements_bacnet_service.txt`

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
BAC0==23.07.03
django==5.2.6
psycopg2-binary==2.9.9
python-dotenv==1.0.0
```

---

### Phase 2: Update Django Service (2-3 hours)

#### Step 2.1: Create BACnet API Client (~1 hour)
**File:** `discovery/bacnet_api_client.py`

```python
"""
BACnet API Client - Communicates with local BACnet service
"""
import requests
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class BACnetAPIClient:
    """Client for communicating with BACnet API service"""

    def __init__(self, base_url: str = "http://host.docker.internal:5001"):
        """
        Initialize client

        Args:
            base_url: Base URL of BACnet API service
                     - Docker: http://host.docker.internal:5001
                     - Local: http://localhost:5001
        """
        self.base_url = base_url
        self.timeout = 30  # 30 second timeout for BACnet operations

    def health_check(self) -> Dict:
        """Check if BACnet service is healthy"""
        try:
            response = requests.get(
                f"{self.base_url}/api/health",
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    def discover_devices(self) -> List[Dict]:
        """
        Discover BACnet devices on network

        Returns:
            List of devices: [{"device_id": 123, "ip_address": "192.168.1.5", "port": 47808}]
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/discover",
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get("devices", [])
        except Exception as e:
            logger.error(f"Device discovery failed: {e}")
            raise

    def discover_device_points(self, device_id: int) -> List[Dict]:
        """
        Discover points for a device

        Args:
            device_id: BACnet device instance number

        Returns:
            List of points: [{"object_type": "analogInput", "instance_number": 1}]
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/devices/{device_id}/points",
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get("points", [])
        except Exception as e:
            logger.error(f"Point discovery failed: {e}")
            raise

    def read_point(self, device_id: int, ip_address: str,
                   object_type: str, instance_number: int) -> Optional[str]:
        """
        Read a single point value

        Args:
            device_id: BACnet device instance
            ip_address: Device IP address
            object_type: BACnet object type (e.g., "analogInput")
            instance_number: Object instance number

        Returns:
            Point value as string, or None if read failed
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/points/read",
                json={
                    "device_id": device_id,
                    "ip_address": ip_address,
                    "object_type": object_type,
                    "instance_number": instance_number
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            if data.get("success"):
                return data.get("value")
            else:
                logger.warning(f"Point read failed: {data.get('error')}")
                return None
        except Exception as e:
            logger.error(f"Point read failed: {e}")
            return None

    def list_virtual_devices(self) -> List[Dict]:
        """List all running virtual devices"""
        try:
            response = requests.get(
                f"{self.base_url}/api/virtual-devices",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data.get("devices", [])
        except Exception as e:
            logger.error(f"Failed to list virtual devices: {e}")
            raise

    def create_virtual_device(self, device_id: int, device_name: str,
                             description: str = "", port: int = 47808) -> Dict:
        """
        Create and start a new virtual BACnet device

        Args:
            device_id: BACnet device instance number (must be unique)
            device_name: Human-readable device name
            description: Optional device description
            port: BACnet UDP port (default 47808)

        Returns:
            Created device information

        Raises:
            requests.HTTPError: If device ID exists or port is in use
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/virtual-devices",
                json={
                    "device_id": device_id,
                    "device_name": device_name,
                    "description": description,
                    "port": port
                },
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to create virtual device: {e}")
            raise

    def get_virtual_device(self, device_id: int) -> Dict:
        """Get details of a virtual device"""
        try:
            response = requests.get(
                f"{self.base_url}/api/virtual-devices/{device_id}",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data.get("device", {})
        except Exception as e:
            logger.error(f"Failed to get virtual device: {e}")
            raise

    def delete_virtual_device(self, device_id: int) -> Dict:
        """Stop and delete a virtual device"""
        try:
            response = requests.delete(
                f"{self.base_url}/api/virtual-devices/{device_id}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to delete virtual device: {e}")
            raise

    def sync_virtual_devices(self) -> Dict:
        """Trigger virtual device sync from database (for background use)"""
        try:
            response = requests.post(
                f"{self.base_url}/api/virtual-devices/sync",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Virtual device sync failed: {e}")
            raise

    # ==================== Virtual Device Points ====================

    def list_device_points(self, device_id: int) -> List[Dict]:
        """List all points in a virtual device"""
        try:
            response = requests.get(
                f"{self.base_url}/api/virtual-devices/{device_id}/points",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data.get("points", [])
        except Exception as e:
            logger.error(f"Failed to list device points: {e}")
            raise

    def add_device_point(self, device_id: int, object_type: str,
                        instance_number: int, object_name: str,
                        present_value: float, description: str = "",
                        units: str = "noUnits", active_text: str = "Active",
                        inactive_text: str = "Inactive") -> Dict:
        """
        Add a point/object to a virtual device

        Args:
            device_id: Virtual device ID
            object_type: analogInput, analogOutput, binaryInput, binaryOutput
            instance_number: BACnet instance number for this point
            object_name: Human-readable name
            present_value: Initial value
            description: Optional description
            units: Engineering units (for analog points)
            active_text: Text for active state (for binary points)
            inactive_text: Text for inactive state (for binary points)

        Returns:
            Created point information
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/virtual-devices/{device_id}/points",
                json={
                    "object_type": object_type,
                    "instance_number": instance_number,
                    "object_name": object_name,
                    "present_value": present_value,
                    "description": description,
                    "units": units,
                    "active_text": active_text,
                    "inactive_text": inactive_text
                },
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to add device point: {e}")
            raise
```

#### Step 2.2: Update UnifiedBACnetService (~1-2 hours)
**File:** `discovery/services/unified_bacnet_service.py`

**Changes:**
1. Replace direct BAC0 calls with BACnetAPIClient calls
2. Keep all database logic intact
3. Add error handling for API communication

```python
from discovery.bacnet_api_client import BACnetAPIClient

class UnifiedBACnetService:
    def __init__(self):
        # Replace BAC0 with API client
        self.api_client = BACnetAPIClient()
        self.device_cache = {}

    def discover_devices(self) -> List[Dict]:
        """Discover devices via API service"""
        try:
            # Check if service is healthy
            health = self.api_client.health_check()
            if health.get("status") != "healthy":
                raise ConnectionError("BACnet API service is not healthy")

            # Call API
            devices = self.api_client.discover_devices()

            # Save to database (existing logic)
            saved_devices = []
            for device_data in devices:
                device = self._save_device(device_data)
                saved_devices.append({
                    "device_id": device.device_id,
                    "ip_address": device.ip_address,
                })

            return saved_devices
        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            raise

    def discover_device_points(self, device: BACnetDevice) -> List:
        """Discover device points via API"""
        try:
            points = self.api_client.discover_device_points(device.device_id)

            # Save to database (existing logic)
            for point_data in points:
                self._save_point(device, point_data)

            return points
        except Exception as e:
            logger.error(f"Point discovery failed: {e}")
            raise

    def read_point_value(self, device: BACnetDevice, point: BACnetPoint) -> Optional[str]:
        """Read point value via API"""
        try:
            value = self.api_client.read_point(
                device_id=device.device_id,
                ip_address=device.ip_address,
                object_type=point.object_type,
                instance_number=point.instance_number
            )

            if value is not None:
                # Save reading to database (existing logic)
                self._save_reading(point, value)

            return value
        except Exception as e:
            logger.error(f"Point read failed: {e}")
            return None
```

#### Step 2.3: Update Virtual Device Views (~30 min)
**File:** `discovery/views.py`

**Update virtual device views to use API client:**

```python
from discovery.bacnet_api_client import BACnetAPIClient

def virtual_device_list(request: HttpRequest) -> HttpResponse:
    """List all virtual devices"""
    try:
        api_client = BACnetAPIClient()
        devices = api_client.list_virtual_devices()

        context = {
            "virtual_devices": devices,
            "total_devices": len(devices),
            "running_devices": len(devices),  # All returned devices are running
        }
        return render(request, "discovery/virtual_device_list.html", context)
    except Exception as e:
        logger.error(f"Failed to list virtual devices: {e}")
        messages.error(request, f"Failed to connect to BACnet service: {e}")
        return render(request, "discovery/virtual_device_list.html", {"virtual_devices": []})

def virtual_device_create(request: HttpRequest) -> HttpResponse:
    """Create new virtual device"""
    if request.method == "POST":
        form = VirtualDeviceCreateForm(request.POST)
        if form.is_valid():
            try:
                api_client = BACnetAPIClient()

                # Create device via API (saves to DB and starts device)
                result = api_client.create_virtual_device(
                    device_id=form.cleaned_data["device_id"],
                    device_name=form.cleaned_data["device_name"],
                    description=form.cleaned_data.get("description", ""),
                    port=form.cleaned_data.get("port", 47808),
                )

                messages.success(
                    request,
                    f"Virtual device {result['device_id']} created and started successfully!"
                )
                return redirect("discovery:virtual_device_list")

            except requests.HTTPError as e:
                # Handle API errors (device ID exists, port in use, etc.)
                error_msg = str(e)
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_data = e.response.json()
                        error_msg = error_data.get('detail', str(e))
                    except:
                        pass
                messages.error(request, f"Failed to create device: {error_msg}")
            except Exception as e:
                messages.error(request, f"Failed to connect to BACnet service: {e}")
    else:
        form = VirtualDeviceCreateForm()

    context = {"form": form}
    return render(request, "discovery/virtual_device_create.html", context)

@csrf_exempt
def virtual_device_delete(request: HttpRequest, device_id: int) -> JsonResponse:
    """Delete virtual device"""
    if request.method == "POST":
        try:
            api_client = BACnetAPIClient()
            result = api_client.delete_virtual_device(device_id)

            return JsonResponse({
                "success": True,
                "message": f"Virtual device {device_id} stopped and deleted successfully"
            })
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return JsonResponse(
                    {"success": False, "message": f"Virtual device {device_id} not found"},
                    status=404
                )
            return JsonResponse(
                {"success": False, "message": str(e)},
                status=500
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"Failed to connect to BACnet service: {e}"},
                status=500
            )

    return JsonResponse(
        {"success": False, "message": "Invalid request method"},
        status=400
    )
```

**Key Changes:**
- ✅ No more `VirtualDeviceService` - all operations via API
- ✅ Device creation happens immediately (no polling delay)
- ✅ Better error handling from API responses
- ✅ Cleaner separation between Django UI and BACnet operations

#### Step 2.4: Add Settings Configuration (~15 min)
**File:** `bacnet_project/settings.py`

```python
# BACnet API Service Configuration
BACNET_API_URL = os.getenv(
    'BACNET_API_URL',
    'http://host.docker.internal:5001'  # Default for Docker
)

# For local development, set in .env:
# BACNET_API_URL=http://localhost:5001
```

---

### Phase 3: Docker Configuration (30 min)

#### Step 3.1: Update docker-compose.yml
**No changes needed!** Django service already configured correctly.

Just ensure it can access `host.docker.internal`:
```yaml
services:
  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    ports:
      - "8000:8000"
    environment:
      - BACNET_API_URL=http://host.docker.internal:5001
    # Docker automatically provides host.docker.internal on Mac/Windows
```

#### Step 3.2: Update .env file
```bash
# BACnet API Service URL
# Docker: http://host.docker.internal:5001
# Local: http://localhost:5001
BACNET_API_URL=http://host.docker.internal:5001
```

---

### Phase 4: Testing & Validation (2 hours)

#### Test 1: BACnet API Service Standalone
```bash
# Terminal 1: Start API service
python bacnet_api_service.py

# Terminal 2: Test endpoints
curl http://localhost:5001/api/health
curl -X POST http://localhost:5001/api/discover
```

**Expected Output:**
```json
{
  "status": "healthy",
  "bacnet_connected": true,
  "local_ip": "192.168.1.5"
}
```

#### Test 2: Django + API Integration
```bash
# Terminal 1: Start PostgreSQL
docker-compose up db

# Terminal 2: Start BACnet API
python bacnet_api_service.py

# Terminal 3: Start Django
docker-compose up web

# Browser: http://localhost:8000
# Click "Discover Devices"
```

**Expected:**
- Discovery finds real devices
- Devices saved to database
- No errors in logs

#### Test 3: Virtual Devices
```bash
# In browser:
# 1. Go to /virtual-devices/create/
# 2. Create virtual device (ID: 1001, Port: 47808)
# 3. API service automatically starts it
# 4. Run discovery - should find virtual device
```

#### Test 4: Virtual Device with Points
```bash
# Terminal: Test API directly
curl -X POST http://localhost:5001/api/virtual-devices \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": 2001,
    "device_name": "Test HVAC",
    "port": 47809
  }'

# Add temperature sensor
curl -X POST http://localhost:5001/api/virtual-devices/2001/points \
  -H "Content-Type: application/json" \
  -d '{
    "object_type": "analogInput",
    "instance_number": 1,
    "object_name": "Room Temperature",
    "present_value": 72.5,
    "units": "degreesCelsius"
  }'

# List points
curl http://localhost:5001/api/virtual-devices/2001/points

# Expected output:
# {
#   "success": true,
#   "device_id": 2001,
#   "points": [
#     {"object_type": "analogInput", "instance_number": 1}
#   ]
# }

# Test BACnet read (from another BACnet client)
# bacnet.read('192.168.1.5:47809 analogInput:1 presentValue')
# Expected: 72.5
```

#### Test 5: Error Handling
**Purpose:** Verify proper error responses and validation

**Test 5a: Duplicate Device ID**
```bash
# Create first device
curl -X POST http://localhost:5001/api/virtual-devices \
  -H "Content-Type: application/json" \
  -d '{"device_id": 3001, "device_name": "Device 1", "port": 47808}'

# Try to create second device with same ID
curl -X POST http://localhost:5001/api/virtual-devices \
  -H "Content-Type: application/json" \
  -d '{"device_id": 3001, "device_name": "Device 2", "port": 47809}'

# Expected: HTTP 400 with error message
# {"detail": "Device ID 3001 already exists"}
```

**Test 5b: Port Conflict**
```bash
# Create first device on port 47808
curl -X POST http://localhost:5001/api/virtual-devices \
  -H "Content-Type: application/json" \
  -d '{"device_id": 3002, "device_name": "Device A", "port": 47808}'

# Try to create second device on same port
curl -X POST http://localhost:5001/api/virtual-devices \
  -H "Content-Type: application/json" \
  -d '{"device_id": 3003, "device_name": "Device B", "port": 47808}'

# Expected: HTTP 400 with error message
# {"detail": "Port 47808 is already in use"}
```

**Test 5c: BACnet Service Down**
```bash
# Stop BACnet API service
# (kill the process)

# Try to discover devices from browser
# Click "Discover Devices" button

# Expected: Error message in browser
# "Failed to connect to BACnet service"
```

**Test 5d: Invalid Object Type**
```bash
# Create device
curl -X POST http://localhost:5001/api/virtual-devices \
  -H "Content-Type: application/json" \
  -d '{"device_id": 3004, "device_name": "Test", "port": 47810}'

# Try to add invalid point type
curl -X POST http://localhost:5001/api/virtual-devices/3004/points \
  -H "Content-Type: application/json" \
  -d '{
    "object_type": "invalidType",
    "instance_number": 1,
    "object_name": "Test",
    "present_value": 0
  }'

# Expected: HTTP 400 with error message
# {"detail": "Unsupported object type: invalidType"}
```

**Test 5e: Device Not Found**
```bash
# Try to add point to non-existent device
curl -X POST http://localhost:5001/api/virtual-devices/99999/points \
  -H "Content-Type: application/json" \
  -d '{
    "object_type": "analogInput",
    "instance_number": 1,
    "object_name": "Test",
    "present_value": 0
  }'

# Expected: HTTP 404
# {"detail": "Device 99999 not running"}
```

**Test 5f: Database Connection Lost**
```bash
# Stop database
docker-compose stop db

# Try to create virtual device from browser
# Fill form and submit

# Expected: Error message
# "Failed to connect to BACnet service" (API can't access DB)

# Restart database
docker-compose start db

# Expected: Service recovers automatically
```

#### Test 6: Delete/Cleanup Operations
**Purpose:** Verify proper cleanup and resource management

**Test 6a: Delete Single Virtual Device**
```bash
# Create device
curl -X POST http://localhost:5001/api/virtual-devices \
  -H "Content-Type: application/json" \
  -d '{"device_id": 4001, "device_name": "Temp Device", "port": 47811}'

# Verify it's running
curl http://localhost:5001/api/virtual-devices

# Delete device
curl -X DELETE http://localhost:5001/api/virtual-devices/4001

# Expected: HTTP 200
# {"success": true, "message": "Virtual device 4001 stopped and deleted"}

# Verify it's gone
curl http://localhost:5001/api/virtual-devices

# Expected: Device 4001 not in list

# Verify port is released (create new device on same port)
curl -X POST http://localhost:5001/api/virtual-devices \
  -H "Content-Type: application/json" \
  -d '{"device_id": 4002, "device_name": "New Device", "port": 47811}'

# Expected: Success (port was properly released)
```

**Test 6b: Delete Virtual Device with Points**
```bash
# Create device with points
curl -X POST http://localhost:5001/api/virtual-devices \
  -H "Content-Type: application/json" \
  -d '{"device_id": 4003, "device_name": "HVAC", "port": 47812}'

# Add multiple points
curl -X POST http://localhost:5001/api/virtual-devices/4003/points \
  -H "Content-Type: application/json" \
  -d '{
    "object_type": "analogInput",
    "instance_number": 1,
    "object_name": "Temperature",
    "present_value": 72.5,
    "units": "degreesCelsius"
  }'

curl -X POST http://localhost:5001/api/virtual-devices/4003/points \
  -H "Content-Type: application/json" \
  -d '{
    "object_type": "analogInput",
    "instance_number": 2,
    "object_name": "Humidity",
    "present_value": 45.0,
    "units": "percent"
  }'

# Verify points exist
curl http://localhost:5001/api/virtual-devices/4003/points

# Delete device
curl -X DELETE http://localhost:5001/api/virtual-devices/4003

# Expected: Device and all points cleaned up
# {"success": true, "message": "Virtual device 4003 stopped and deleted"}
```

**Test 6c: Delete from Web Interface**
```bash
# In browser:
# 1. Go to /virtual-devices/
# 2. Click "Delete" button on a virtual device
# 3. Confirm deletion

# Expected:
# - Success message appears
# - Device removed from list
# - BACnet service stops device
# - Port released
```

**Test 6d: Bulk Cleanup**
```bash
# Create multiple devices
for i in {5001..5005}; do
  port=$((47813 + i - 5001))
  curl -X POST http://localhost:5001/api/virtual-devices \
    -H "Content-Type: application/json" \
    -d "{\"device_id\": $i, \"device_name\": \"Device $i\", \"port\": $port}"
done

# Verify all running
curl http://localhost:5001/api/virtual-devices

# Expected: 5 devices listed

# Delete all devices
for i in {5001..5005}; do
  curl -X DELETE http://localhost:5001/api/virtual-devices/$i
done

# Verify all gone
curl http://localhost:5001/api/virtual-devices

# Expected: Empty list or no devices
```

**Test 6e: Service Restart Recovery**
```bash
# Create devices
curl -X POST http://localhost:5001/api/virtual-devices \
  -H "Content-Type: application/json" \
  -d '{"device_id": 6001, "device_name": "Device A", "port": 47820}'

curl -X POST http://localhost:5001/api/virtual-devices \
  -H "Content-Type: application/json" \
  -d '{"device_id": 6002, "device_name": "Device B", "port": 47821}'

# Stop BACnet API service (Ctrl+C)

# Restart BACnet API service
python bacnet_api_service.py

# Expected:
# - Background sync loop starts
# - Devices with is_running=True in database are restarted
# - Both devices come back online within 10 seconds

# Verify devices running
curl http://localhost:5001/api/virtual-devices

# Expected: Both devices in list
```

**Test 6f: Database Cleanup on Delete**
```bash
# Create device
curl -X POST http://localhost:5001/api/virtual-devices \
  -H "Content-Type: application/json" \
  -d '{"device_id": 7001, "device_name": "Test", "port": 47825}'

# Verify in database (from Django shell)
docker-compose exec web python manage.py shell
>>> from discovery.models import VirtualBACnetDevice
>>> VirtualBACnetDevice.objects.filter(device_id=7001).exists()
True
>>> exit()

# Delete via API
curl -X DELETE http://localhost:5001/api/virtual-devices/7001

# Check database again
docker-compose exec web python manage.py shell
>>> from discovery.models import VirtualBACnetDevice
>>> VirtualBACnetDevice.objects.filter(device_id=7001).exists()
False
>>> exit()

# Expected: Database record deleted
```

#### Test 7: Cross-Platform
**Mac:**
```bash
docker-compose up db web
python bacnet_api_service.py
```

**Windows:**
```bash
docker-compose up db web
python bacnet_api_service.py
```

**Both should work identically!**

---

### Test Coverage Summary

| Test # | Category | Sub-tests | What's Tested |
|--------|----------|-----------|---------------|
| **Test 1** | API Standalone | 1 | Health check, basic discovery |
| **Test 2** | Integration | 1 | Django + API + Database |
| **Test 3** | Virtual Devices | 1 | Device creation via web UI |
| **Test 4** | Points | 1 | Point creation & BACnet reading |
| **Test 5** | Error Handling | **6** | Validation, conflicts, recovery |
| **Test 6** | Cleanup | **6** | Delete operations, resource release |
| **Test 7** | Cross-Platform | 2 | Mac/Windows consistency |

**Total Test Cases: 18**

### Error Handling Coverage
✅ Duplicate device ID
✅ Port conflicts
✅ Service unavailable
✅ Invalid input validation
✅ Resource not found (404)
✅ Database connection loss/recovery

### Cleanup Coverage
✅ Single device deletion
✅ Device with points deletion
✅ Web UI deletion
✅ Bulk deletion (5+ devices)
✅ Service restart recovery
✅ Database cascade cleanup

---

## 📂 Project File Structure

**Single Repository Structure (Option 1 - Chosen)**

```
BACnet_django/                      # Project root
│
├── bacnet_api_service.py           # 🆕 FastAPI BACnet API service (runs on host)
├── requirements_bacnet_service.txt # 🆕 BACnet service dependencies
│
├── manage.py                       # Django management
├── docker-compose.yml              # Docker services (db, web)
├── requirements.txt                # Django dependencies
├── Dockerfile                      # Django container
├── .env                            # Environment variables
├── .env.example                    # 🔄 Update with BACNET_API_URL
├── .gitignore                      # Git ignore rules
├── README.md                       # 🔄 Update with new architecture
│
├── bacnet_project/                 # Django project settings
│   ├── __init__.py
│   ├── settings.py                 # 🔄 Add BACNET_API_URL config
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── discovery/                      # Main Django app
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                   # BACnetDevice, BACnetPoint, VirtualBACnetDevice
│   ├── views.py                    # 🔄 Update to use bacnet_api_client
│   ├── urls.py
│   ├── forms.py                    # VirtualDeviceCreateForm
│   ├── bacnet_api_client.py       # 🆕 Client for BACnet API service
│   ├── virtual_device_service.py  # ⚠️ Deprecated (use API instead)
│   ├── exceptions.py               # BACnet exceptions
│   ├── constants.py                # BACnet constants
│   │
│   ├── services/                   # Service layer
│   │   └── unified_bacnet_service.py  # 🔄 Update to use API client
│   │
│   ├── management/                 # Management commands
│   │   └── commands/
│   │       ├── discover_devices.py
│   │       ├── collect_readings.py
│   │       └── run_virtual_devices.py  # ⚠️ Deprecated (use API instead)
│   │
│   ├── templates/                  # Django templates
│   │   └── discovery/
│   │       ├── dashboard.html
│   │       ├── device_detail.html
│   │       ├── virtual_device_list.html
│   │       └── virtual_device_create.html
│   │
│   ├── migrations/                 # Database migrations
│   │   └── ...
│   │
│   └── tests/                      # Test files
│       └── ...
│
├── static/                         # Static files
│   └── ...
│
├── media/                          # Media files
│   └── ...
│
├── TODO/                           # Project documentation
│   ├── 10-13_bacnet-api-service-architecture.md  # This file
│   ├── 10-08_virtual-device-implementation-summary.md
│   └── ...
│
└── docs/                           # Additional documentation (optional)
    └── ...
```

### Key Files by Location

**Project Root (Run on Host):**
- `bacnet_api_service.py` - BACnet operations (discovery, reading, virtual devices)
- `requirements_bacnet_service.txt` - FastAPI, BAC0, Django (for DB access)

**Docker Services:**
- `docker-compose.yml` - Database + Web services
- `requirements.txt` - Django, DRF, psycopg2

**Django App (discovery/):**
- `bacnet_api_client.py` - Client to communicate with BACnet API
- `views.py` - Web interface (uses API client)
- `services/unified_bacnet_service.py` - Service layer (uses API client)

### What Gets Deprecated

**Files no longer needed:**
- ❌ `windows_integrated_server.py` - Replaced by bacnet_api_service.py
- ❌ `docker-compose.windows.yml` - Use main docker-compose.yml
- ❌ `discovery/virtual_device_service.py` - Logic moved to API service
- ❌ `discovery/management/commands/run_virtual_devices.py` - Replaced by API

**Keep for reference but mark deprecated:**
- ⚠️ Old service files (keep for rollback if needed)

---

## 📦 Deliverables

### New Files Created
- ✅ `bacnet_api_service.py` (root) - FastAPI service for BACnet operations
- ✅ `discovery/bacnet_api_client.py` - Django client for API communication
- ✅ `requirements_bacnet_service.txt` (root) - API service dependencies

### Modified Files
- ✅ `discovery/views.py` - Update virtual device views to use API client
- ✅ `discovery/services/unified_bacnet_service.py` - Use API client instead of direct BAC0
- ✅ `bacnet_project/settings.py` - Add BACNET_API_URL setting
- ✅ `.env.example` - Add BACNET_API_URL example
- ✅ `README.md` - Update setup instructions

### Deprecated Files (Keep but don't use)
- ⚠️ `windows_integrated_server.py` - Use bacnet_api_service.py instead
- ⚠️ `docker-compose.windows.yml` - Use docker-compose.yml instead
- ⚠️ `discovery/virtual_device_service.py` - Logic in API service now
- ⚠️ `discovery/management/commands/run_virtual_devices.py` - API manages devices now

---

## 📅 Implementation Timeline

### Day 1: BACnet API Service (5-6 hours)
- **Hour 1-2**: Create FastAPI service with discovery and reading
- **Hour 3**: Add virtual device management (create/delete/list)
- **Hour 4**: Add virtual device point management (add/list points)
- **Hour 5**: Test standalone service
- **Hour 6**: Documentation and error handling

### Day 2: Django Integration (3-4 hours)
- **Hour 1**: Create BACnetAPIClient with all methods
- **Hour 2**: Update UnifiedBACnetService
- **Hour 3**: Update virtual device views
- **Hour 4**: Configuration and basic testing

### Day 3: Testing & Documentation (2-3 hours)
- **Hour 1**: Test virtual device creation with points
- **Hour 2**: Cross-platform testing (Mac/Windows)
- **Hour 3**: Update README and documentation

**Total Time: 10-13 hours (1.5-2 days)**

**Note:** Point management adds ~2-3 hours but significantly improves virtual device realism and testing capabilities.

---

## 🎯 Success Criteria

### Functional Requirements
- ✅ Device discovery works via API
- ✅ Point discovery works via API
- ✅ Point reading works via API
- ✅ Virtual devices start automatically
- ✅ Virtual device points can be added/listed
- ✅ Points respond to BACnet read requests
- ✅ Health check endpoint responds
- ✅ Error handling and logging

### Architecture Requirements
- ✅ Django has no direct BAC0 dependencies
- ✅ All BACnet operations in API service
- ✅ Clean API contracts (OpenAPI/Swagger)
- ✅ Mac and Windows have identical setup

### Testing Requirements
- ✅ All existing tests still pass
- ✅ Can mock API client for unit tests
- ✅ Integration tests with real API
- ✅ Cross-platform validation

---

## 🚀 Deployment Instructions

### Development (Mac/Windows)
```bash
# Terminal 1: Database + Web
docker-compose up

# Terminal 2: BACnet API Service
python bacnet_api_service.py

# Access: http://localhost:8000
```

### Production (Linux)
```bash
# Option 1: Run API service in Docker with network_mode: host
docker-compose -f docker-compose.prod.yml up

# Option 2: Run API service on host, web in Docker
docker-compose up db web
python bacnet_api_service.py
```

---

## 📊 Architecture Comparison

### Before (Tightly Coupled)
```
Components: Django (with BAC0) + PostgreSQL
Deployment: Different per platform
Testing: Hard to mock BACnet
Scalability: Limited
Network Issues: Docker networking problems
```

### After (Clean Separation)
```
Components: Django + BACnet API + PostgreSQL
Deployment: Consistent across platforms
Testing: Easy to mock API
Scalability: Independent scaling
Network Issues: Solved (API runs on host)
```

---

## 🔄 Virtual Device Creation Flow

### End-to-End Flow Diagram
```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: User Creates Virtual Device in Browser            │
│  URL: http://localhost:8000/virtual-devices/create/        │
│  Form: Device ID=1001, Name="Test HVAC", Port=47808        │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP POST
┌──────────────────────▼──────────────────────────────────────┐
│  Step 2: Django View (virtual_device_create)                │
│  - Validates form                                           │
│  - Calls: api_client.create_virtual_device()               │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP POST to http://localhost:5001/api/virtual-devices
┌──────────────────────▼──────────────────────────────────────┐
│  Step 3: BACnet API Service (bacnet_api_service.py)        │
│  - Validates device ID is unique                            │
│  - Validates port is available                              │
│  - Creates VirtualBACnetDevice in database                  │
│  - Starts BAC0.lite(deviceId=1001, port=47808)             │
│  - Adds to running_virtual_devices dictionary               │
└──────────────────────┬──────────────────────────────────────┘
                       │ Returns: {"device_id": 1001, "is_running": true}
┌──────────────────────▼──────────────────────────────────────┐
│  Step 4: Django View receives response                      │
│  - Shows success message: "Device 1001 created!"            │
│  - Redirects to /virtual-devices/                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│  Step 5: Virtual Device Running                             │
│  - Device 1001 listening on 192.168.1.5:47808               │
│  - Responds to BACnet WhoIs broadcasts                      │
│  - Can be discovered by other BACnet clients                │
└─────────────────────────────────────────────────────────────┘
```

### Benefits of This Flow
- ✅ **Immediate feedback**: Device starts instantly when created
- ✅ **No polling delay**: Unlike old run_virtual_devices polling (every 5 seconds)
- ✅ **Better error handling**: API returns specific errors (ID exists, port in use)
- ✅ **Consistent with other operations**: All BACnet ops through API
- ✅ **Clean separation**: Django never touches BAC0 directly

### Port Assignment Strategy
**First device (standard port):**
- Device ID: 1001, Port: 47808 ✅ (BACnet standard)

**Second device (auto-increment):**
- Device ID: 1002, Port: 47809 ✅ (47808 already in use)

**Third device:**
- Device ID: 1003, Port: 47810 ✅ (47808, 47809 in use)

**Why different ports?**
- Multiple virtual devices on same machine need unique ports
- Real BACnet devices use same port (47808) but different IPs
- Virtual devices share same IP, require different ports

---

## 🔧 Virtual Device Points/Objects

### What are BACnet Points?
BACnet points are the actual data objects in a device:
- **Analog Input**: Temperature sensors, humidity sensors, power meters
- **Analog Output**: Setpoints, dimmer levels, valve positions
- **Binary Input**: Door sensors, motion detectors, alarm states
- **Binary Output**: Fan controls, light switches, pump controls

### Why Add Points to Virtual Devices?
**Without points:**
- Device responds to WhoIs but has no data
- Not realistic for testing
- Discovery tools see empty device

**With points:**
- Device behaves like real BACnet equipment
- Can test reading, writing, trending
- Realistic integration testing

### API Implementation Example

**Create virtual HVAC device with points:**
```python
# Step 1: Create virtual device
POST /api/virtual-devices
{
  "device_id": 1001,
  "device_name": "HVAC Controller",
  "port": 47808
}

# Step 2: Add temperature sensor (analog input)
POST /api/virtual-devices/1001/points
{
  "object_type": "analogInput",
  "instance_number": 1,
  "object_name": "Room Temperature",
  "present_value": 72.5,
  "units": "degreesCelsius",
  "description": "Room temperature sensor"
}

# Step 3: Add humidity sensor
POST /api/virtual-devices/1001/points
{
  "object_type": "analogInput",
  "instance_number": 2,
  "object_name": "Room Humidity",
  "present_value": 45.0,
  "units": "percent",
  "description": "Room humidity sensor"
}

# Step 4: Add fan control (binary output)
POST /api/virtual-devices/1001/points
{
  "object_type": "binaryOutput",
  "instance_number": 1,
  "object_name": "Fan",
  "present_value": 0,
  "description": "Fan on/off control",
  "active_text": "On",
  "inactive_text": "Off"
}

# Result: Virtual HVAC with 3 controllable points
# - analogInput:1 (Temperature: 72.5°C)
# - analogInput:2 (Humidity: 45%)
# - binaryOutput:1 (Fan: Off)
```

### BAC0 Implementation Details

**Using BAC0 local objects:**
```python
from BAC0.core.devices.local.models import (
    analog_input, analog_output,
    binary_input, binary_output
)

# When creating virtual device
bacnet_device = BAC0.lite(
    deviceId=1001,
    port=47808,
    localObjName="HVAC Controller"
)

# Add analog input (temperature sensor)
temp_sensor = analog_input(
    name="Room Temperature",
    description="Room temperature sensor",
    presentValue=72.5,
    units="degreesCelsius"
)

# Register with device
temp_sensor.add_objects_to_application(bacnet_device)

# Now device has:
# - device:1001 (device object)
# - analogInput:1 (temperature sensor)
```

### Point Types Reference

| Object Type | Use Case | Properties |
|-------------|----------|------------|
| **analogInput** | Sensors (temp, humidity, power) | presentValue, units, description |
| **analogOutput** | Setpoints, dimmer levels | presentValue, units, relinquishDefault |
| **binaryInput** | Door sensors, alarms | presentValue, activeText, inactiveText |
| **binaryOutput** | Switches, fan controls | presentValue, activeText, inactiveText |

### Full Example: Create Complete Virtual Device

```python
# API Request Body
{
  "device_id": 2001,
  "device_name": "Lighting Panel",
  "port": 47809,
  "points": [
    {
      "object_type": "binaryOutput",
      "instance_number": 1,
      "object_name": "Main Lights",
      "present_value": 0,
      "active_text": "On",
      "inactive_text": "Off"
    },
    {
      "object_type": "analogOutput",
      "instance_number": 1,
      "object_name": "Dimmer Level",
      "present_value": 0.0,
      "units": "percent"
    },
    {
      "object_type": "binaryInput",
      "instance_number": 1,
      "object_name": "Occupancy Sensor",
      "present_value": 0,
      "active_text": "Occupied",
      "inactive_text": "Vacant"
    }
  ]
}

# Creates lighting panel with:
# - Switch control (on/off)
# - Dimmer control (0-100%)
# - Occupancy sensor (occupied/vacant)
```

---

## 🔧 Configuration Reference

### Environment Variables
```bash
# Django (.env)
DATABASE_URL=postgresql://user:pass@localhost:5432/bacnet_db
SECRET_KEY=your-secret-key
DEBUG=True
BACNET_API_URL=http://host.docker.internal:5001

# BACnet API Service (optional)
BACNET_PORT=47808
LOG_LEVEL=INFO
```

### API Endpoints Reference
```
# Service Health
GET    /api/health                      → Health check
GET    /docs                            → Swagger UI (interactive documentation)

# Device Discovery & Reading
POST   /api/discover                    → Discover BACnet devices on network
GET    /api/devices                     → List discovered devices (cached)
POST   /api/devices/{id}/points         → Discover points for device
POST   /api/devices/{id}/read           → Read all points from device
POST   /api/points/read                 → Read single point value

# Virtual Device Management
GET    /api/virtual-devices             → List running virtual devices
POST   /api/virtual-devices             → Create + start new virtual device
GET    /api/virtual-devices/{id}        → Get virtual device details
DELETE /api/virtual-devices/{id}        → Stop + delete virtual device
POST   /api/virtual-devices/sync        → Sync from database (background)

# Virtual Device Points/Objects
GET    /api/virtual-devices/{id}/points → List points in virtual device
POST   /api/virtual-devices/{id}/points → Add point/object to virtual device
DELETE /api/virtual-devices/{id}/points/{point_id} → Remove point from device
```

---

## 📝 Next Steps After Implementation

1. **Phase 2 Enhancements:**
   - Add write operations (control outputs)
   - Implement Change of Value (COV) subscriptions
   - Add BACnet priority arrays

2. **Performance Optimization:**
   - Add Redis caching for device lists
   - Implement connection pooling
   - Optimize bulk reading operations

3. **Production Hardening:**
   - Add authentication to API
   - Implement rate limiting
   - Add metrics and monitoring
   - Create systemd service files

---

## 🎓 Learning Outcomes

This implementation demonstrates:
- ✅ Microservices architecture
- ✅ API-first design
- ✅ Clean separation of concerns
- ✅ Cross-platform deployment
- ✅ Professional software engineering practices

**Perfect for internship portfolio!**

---

**Status:** Ready to implement
**Dependencies:** FastAPI, BAC0, Django, PostgreSQL
**Risk Level:** Low (can rollback to current implementation)
**Expected Completion:** 1-1.5 days (8-10 hours)
