"""
BACnet API Service - FastAPI service for BACnet operations

This service provides HTTP API endpoints for BACnet operations, running on the
host network with full access to BACnet UDP broadcasts. It separates BACnet
hardware operations from the Django web interface.

Architecture:
- Runs on host network (not in Docker)
- Provides REST API for BACnet operations
- Manages virtual BACnet devices
- Access Django database for device/point storage

API Endpoints:
- GET  /api/health                     - Health check
- POST /api/discover                   - Discover BACnet devices
- POST /api/devices/{id}/points        - Discover device points
- POST /api/points/read                - Read single point
- GET  /api/virtual-devices            - List virtual devices
- POST /api/virtual-devices            - Create virtual device
- GET  /api/virtual-devices/{id}       - Get virtual device
- DELETE /api/virtual-devices/{id}     - Delete virtual device
- GET  /api/virtual-devices/{id}/points - List device points
- POST /api/virtual-devices/{id}/points - Add device point

Usage:
    python bacnet_api_service.py

    Access API docs: http://localhost:5001/docs
"""

import asyncio
import logging
import os
import platform
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

# BACnet imports
import BAC0
from asgiref.sync import sync_to_async
from BAC0.core.devices.local import factory

# FastAPI imports
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import factory functions
analog_input = factory.analog_input
analog_output = factory.analog_output
binary_input = factory.binary_input
binary_output = factory.binary_output
character_string = factory.character_string
multistate_value = factory.multistate_value

# Django setup for database access
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bacnet_project.settings")
import django  # noqa: E402

django.setup()

from discovery.models import VirtualBACnetDevice  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# FastAPI app will be created after lifespan function is defined

# Global state
bacnet_instance = None
discovered_devices_cache = {}
running_virtual_devices = {}
virtual_device_points = {}


# ==================== Helper Functions ====================


def get_bacnet_ip() -> str:
    """
    Get BACnet interface IP based on operating system or environment variable.

    Priority:
    1. BACNET_INTERFACE_IP environment variable (manual override)
    2. Auto-detect based on OS:
       - macOS (Darwin) -> 192.168.1.101/24 (home)
       - Windows -> 192.168.1.5/24 (office)

    Returns:
        str: IP address with CIDR notation (e.g., "192.168.1.101/24")

    Raises:
        RuntimeError: If unsupported OS and no environment variable set
    """
    # Check environment variable first (manual override)
    env_ip = os.getenv("BACNET_INTERFACE_IP")
    if env_ip:
        logger.info(f"🌐 Using BACnet IP from environment: {env_ip}")
        return env_ip

    # Auto-detect based on OS
    system = platform.system()

    if system == "Darwin":  # macOS
        ip = "192.168.1.101/24"
        logger.info(f"🍎 Detected macOS - Using home network: {ip}")
        return ip

    elif system == "Windows":  # Windows
        ip = "192.168.1.5/24"
        logger.info(f"🪟 Detected Windows - Using office network: {ip}")
        return ip

    else:  # Linux or other
        logger.error(f"❌ Unsupported platform: {system}")
        raise RuntimeError(
            f"Unsupported platform: {system}. "
            f"Please set BACNET_INTERFACE_IP environment variable."
        )


# ==================== Pydantic Models ====================


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


class VirtualDevicePointCreate(BaseModel):
    object_type: str  # analogInput, analogOutput, binaryInput, binaryOutput
    instance_number: int
    object_name: str
    present_value: float
    description: str = ""
    units: str = "noUnits"
    active_text: str = "Active"
    inactive_text: str = "Inactive"


# ==================== Startup/Shutdown Events ====================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    global bacnet_instance
    # Startup
    try:
        # Main instance is BOTH a client AND a device
        # Get IP based on OS or environment variable
        bacnet_ip = get_bacnet_ip()

        bacnet_instance = BAC0.lite(
            ip=bacnet_ip, deviceId=1000, localObjName="BACnet API Device", port=47808
        )
        logger.info(
            f"✅ BAC0 started as device 1000 on {bacnet_instance.localIPAddr}:47808"
        )

        # Add default points to device 1000 using factory pattern
        try:
            # Create ObjectFactory instances
            temp_obj = factory.analog_input(
                name="Temperature",
                description="Room temperature sensor",
                properties={"units": "degreesFahrenheit"},
                presentValue=72.5,
                is_commandable=False,
            )

            humidity_obj = factory.analog_input(
                name="Humidity",
                description="Room humidity sensor",
                properties={"units": "percentRelativeHumidity"},
                presentValue=45.0,
                is_commandable=False,
            )

            fan_obj = factory.binary_input(
                name="FanStatus",
                description="Fan running status",
                properties={"activeText": "Running", "inactiveText": "Stopped"},
                presentValue=0,
                is_commandable=False,
            )

            # Add objects to the device
            temp_obj.add_objects_to_application(bacnet_instance)
            humidity_obj.add_objects_to_application(bacnet_instance)
            fan_obj.add_objects_to_application(bacnet_instance)

            logger.info(
                "✅ Added 3 default points to device 1000 using factory pattern"
            )
        except Exception as e:
            logger.warning(f"⚠️ Could not add default points: {e}")

        # Virtual device sync disabled (focusing on device 1000 as client only)
        # sync_task = asyncio.create_task(virtual_device_sync_loop())
        # logger.info("✅ Background virtual device sync started")

        yield  # Server is running

    finally:
        # Shutdown
        if bacnet_instance:
            bacnet_instance.disconnect()
            logger.info("✅ BAC0 disconnected")


# Create FastAPI app with lifespan
app = FastAPI(
    title="BACnet API Service",
    description="BACnet operations API for Django web application",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Health Check ====================


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "bacnet_connected": bacnet_instance is not None,
        "main_device_id": 1000,
        "main_device_port": 47808,
        "local_ip": str(bacnet_instance.localIPAddr) if bacnet_instance else None,
        "additional_virtual_devices": len(running_virtual_devices),
    }


# ==================== Device Discovery ====================


@app.post("/api/discover", response_model=DiscoveryResponse)
async def discover_devices():
    """Discover BACnet devices on network"""
    try:
        # Trigger Who-Is broadcast
        bacnet_instance.discover()

        # Wait for I-Am responses (BACnet devices need time to respond)
        logger.info("⏳ Waiting 5 seconds for device responses...")
        await asyncio.sleep(5)

        # Get discovered devices from BAC0's known_devices or device info cache
        devices = []

        # Access device_info_cache directly through this_application
        # The DeviceInfoCache logs show devices are being registered there
        try:
            if hasattr(bacnet_instance, "this_application"):
                app = bacnet_instance.this_application
                if hasattr(app, "device_info_cache"):
                    cache = app.device_info_cache
                    logger.info("DEBUG: Accessing device_info_cache")

                    # The cache is a dict-like object
                    if hasattr(cache, "__iter__"):
                        for device_key in cache:
                            device_info = cache[device_key]
                            logger.info(
                                f"DEBUG: Found device_key={device_key}, "
                                f"info={device_info}"
                            )

                            # Extract device ID and address
                            if hasattr(device_info, "device_identifier"):
                                device_id = device_info.device_identifier[1]
                                address = str(device_info.address)
                                # Remove port if present
                                # (e.g., "192.168.1.207:47808" -> "192.168.1.207")
                                if ":" in address:
                                    address = address.split(":")[0]
                                devices.append((address, device_id))
                                logger.info(f"✅ Found device {device_id} at {address}")
        except Exception as e:
            logger.error(f"Error accessing device_info_cache: {e}", exc_info=True)

        # Handle None or empty result
        if not devices:
            logger.info("✅ Discovery completed: 0 devices found")
            return DiscoveryResponse(success=True, devices=[], count=0)

        # Convert to Django-compatible format
        device_list = []
        for device in devices:
            try:
                # BAC0 returns tuples in various formats:
                # 2-tuple: (address, device_id)
                # 3-tuple: (address, port, device_id)
                if isinstance(device, tuple):
                    if len(device) == 2:
                        # Format: (IP, device_id)
                        ip_addr = device[0]
                        device_id = device[1]
                        # Skip invalid formats
                        if ":" in str(ip_addr) and "." not in str(ip_addr):
                            logger.warning(f"⚠️ Invalid IP format: {device}")
                            continue
                        device_list.append(
                            {
                                "device_id": device_id,
                                "ip_address": ip_addr,
                                "port": 47808,  # Default BACnet port
                            }
                        )
                    elif len(device) >= 3:
                        # Format: (IP, port, device_id)
                        device_list.append(
                            {
                                "device_id": device[2],
                                "ip_address": device[0],
                                "port": device[1],
                            }
                        )
                    else:
                        logger.warning(f"⚠️ Unexpected device format: {device}")
                else:
                    logger.warning(f"⚠️ Device is not a tuple: {device}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to parse device {device}: {e}")
                continue

        # Cache results
        global discovered_devices_cache
        discovered_devices_cache = {d["device_id"]: d for d in device_list}

        logger.info(f"✅ Discovered {len(device_list)} devices")

        return DiscoveryResponse(
            success=True, devices=device_list, count=len(device_list)
        )
    except Exception as e:
        logger.error(f"❌ Discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/devices/{device_id}/points")
async def discover_device_points(device_id: int):
    """Discover points for a specific device"""
    try:
        # Get device from cache or require IP
        if device_id not in discovered_devices_cache:
            raise HTTPException(
                status_code=404, detail="Device not found. Run discovery first."
            )

        device_info = discovered_devices_cache[device_id]
        device_address = f"{device_info['ip_address']}:{device_info['port']}"

        # Read object list
        object_list = bacnet_instance.read(
            f"{device_address} device {device_id} objectList"
        )

        # Parse and return
        points = []
        for obj in object_list:
            obj_type, obj_instance = obj.split(":")
            points.append(
                {"object_type": obj_type, "instance_number": int(obj_instance)}
            )

        logger.info(f"✅ Discovered {len(points)} points for device {device_id}")

        return {
            "success": True,
            "device_id": device_id,
            "points": points,
            "count": len(points),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Point discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Point Reading ====================


@app.post("/api/points/read", response_model=PointReadResponse)
async def read_point(request: PointReadRequest):
    """Read a single BACnet point value"""
    try:
        address = (
            f"{request.ip_address} {request.object_type} "
            f"{request.instance_number} presentValue"
        )
        value = bacnet_instance.read(address)

        logger.info(
            f"✅ Read {request.object_type}:{request.instance_number} = {value}"
        )

        return PointReadResponse(success=True, value=str(value), error=None)
    except Exception as e:
        logger.error(f"❌ Point read failed: {e}")
        return PointReadResponse(success=False, value=None, error=str(e))


# ==================== Virtual Device Management ====================


@app.get("/api/virtual-devices")
async def list_virtual_devices():
    """List all running virtual devices"""
    try:
        devices = []
        for device_id, bacnet_device in running_virtual_devices.items():
            # Get from database (async-safe)
            db_device = await get_device_from_db(device_id)
            devices.append(
                {
                    "device_id": db_device.device_id,
                    "device_name": db_device.device_name,
                    "description": db_device.description,
                    "port": db_device.port,
                    "is_running": True,
                    "local_ip": str(bacnet_device.localIPAddr),
                }
            )

        logger.info(f"📋 Listed {len(devices)} virtual devices")

        return {"success": True, "devices": devices, "count": len(devices)}
    except Exception as e:
        logger.error(f"❌ Failed to list virtual devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@sync_to_async
def check_device_exists(device_id: int) -> bool:
    """Check if device exists in database (sync function)"""
    return VirtualBACnetDevice.objects.filter(device_id=device_id).exists()


@sync_to_async
def create_device_in_db(device_id: int, device_name: str, description: str, port: int):
    """Create device in database (sync function)"""
    return VirtualBACnetDevice.objects.create(
        device_id=device_id,
        device_name=device_name,
        description=description,
        port=port,
        is_running=True,
    )


@app.post("/api/virtual-devices", response_model=VirtualDeviceResponse)
async def create_virtual_device(request: VirtualDeviceCreate):
    """Create and start a new virtual BACnet device"""
    try:
        # Check if device ID already exists (async-safe)
        if await check_device_exists(request.device_id):
            raise HTTPException(
                status_code=400, detail=f"Device ID {request.device_id} already exists"
            )

        # Check if port is in use
        for device_id, bacnet_dev in running_virtual_devices.items():
            if hasattr(bacnet_dev, "port") and bacnet_dev.port == request.port:
                raise HTTPException(
                    status_code=400, detail=f"Port {request.port} is already in use"
                )

        # Create in database (async-safe)
        device = await create_device_in_db(
            request.device_id, request.device_name, request.description, request.port
        )

        # Start virtual BACnet device
        # Get IP based on OS or environment variable
        bacnet_ip = get_bacnet_ip()

        bacnet_device = BAC0.lite(
            ip=bacnet_ip,
            deviceId=device.device_id,
            port=device.port,
            localObjName=device.device_name,
        )
        running_virtual_devices[device.device_id] = bacnet_device

        logger.info(
            f"✅ Virtual device {device.device_id} created and started "
            f"on port {device.port}"
        )

        return VirtualDeviceResponse(
            device_id=device.device_id,
            device_name=device.device_name,
            description=device.description,
            port=device.port,
            is_running=True,
            created_at=device.created_at.isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to create virtual device: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@sync_to_async
def get_device_from_db(device_id: int):
    """Get device from database (sync function)"""
    return VirtualBACnetDevice.objects.get(device_id=device_id)


@app.get("/api/virtual-devices/{device_id}")
async def get_virtual_device(device_id: int):
    """Get details of a virtual device"""
    try:
        device = await get_device_from_db(device_id)
        is_running = device_id in running_virtual_devices

        response = {
            "device_id": device.device_id,
            "device_name": device.device_name,
            "description": device.description,
            "port": device.port,
            "is_running": is_running,
            "created_at": device.created_at.isoformat(),
            "updated_at": device.updated_at.isoformat(),
        }

        if is_running:
            bacnet_device = running_virtual_devices[device_id]
            response["local_ip"] = str(bacnet_device.localIPAddr)

        return {"success": True, "device": response}
    except VirtualBACnetDevice.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    except Exception as e:
        logger.error(f"❌ Failed to get virtual device: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@sync_to_async
def delete_device_from_db(device_id: int):
    """Delete device from database (sync function)"""
    device = VirtualBACnetDevice.objects.get(device_id=device_id)
    device.delete()


@app.delete("/api/virtual-devices/{device_id}")
async def delete_virtual_device(device_id: int):
    """Stop and delete a virtual device"""
    try:
        # Stop if running
        if device_id in running_virtual_devices:
            running_virtual_devices[device_id].disconnect()
            del running_virtual_devices[device_id]
            logger.info(f"⏹️ Virtual device {device_id} stopped")

        # Delete from database (async-safe)
        await delete_device_from_db(device_id)

        logger.info(f"🗑️ Virtual device {device_id} deleted")

        return {
            "success": True,
            "message": f"Virtual device {device_id} stopped and deleted",
        }
    except VirtualBACnetDevice.DoesNotExist:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    except Exception as e:
        logger.error(f"❌ Failed to delete virtual device: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Virtual Device Points ====================


@app.get("/api/virtual-devices/{device_id}/points")
async def list_virtual_device_points(device_id: int):
    """List all points in a virtual device (including main device 1000)"""
    try:
        # Check if it's the main device or a virtual device
        if device_id == 1000:
            bacnet_device = bacnet_instance
        elif device_id in running_virtual_devices:
            bacnet_device = running_virtual_devices[device_id]
        else:
            raise HTTPException(
                status_code=404, detail=f"Device {device_id} not running"
            )

        # Get object list from BAC0 device
        points = []
        if hasattr(bacnet_device, "this_application") and hasattr(
            bacnet_device.this_application, "objectList"
        ):
            for obj in bacnet_device.this_application.objectList:
                if obj[0] != "device":  # Skip device object
                    points.append(
                        {
                            "object_type": obj[0],
                            "instance_number": obj[1],
                        }
                    )

        logger.info(f"📋 Listed {len(points)} points for device {device_id}")

        return {
            "success": True,
            "device_id": device_id,
            "points": points,
            "count": len(points),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to list points: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/virtual-devices/{device_id}/points")
async def add_virtual_device_point(device_id: int, request: VirtualDevicePointCreate):
    """Add a point/object to a virtual device (including main device 1000)"""
    try:
        # Check if it's the main device or a virtual device
        if device_id == 1000:
            bacnet_device = bacnet_instance
        elif device_id in running_virtual_devices:
            bacnet_device = running_virtual_devices[device_id]
        else:
            raise HTTPException(
                status_code=404, detail=f"Device {device_id} not running"
            )

        # Create appropriate point type
        point_obj = None

        if request.object_type == "analogInput":
            point_obj = analog_input(
                instance=request.instance_number,
                name=request.object_name,
                description=request.description,
                presentValue=request.present_value,
                units=request.units,
            )
        elif request.object_type == "analogOutput":
            point_obj = analog_output(
                instance=request.instance_number,
                name=request.object_name,
                description=request.description,
                presentValue=request.present_value,
                units=request.units,
            )
        elif request.object_type == "binaryInput":
            point_obj = binary_input(
                instance=request.instance_number,
                name=request.object_name,
                description=request.description,
                presentValue=int(request.present_value),
                activeText=request.active_text,
                inactiveText=request.inactive_text,
            )
        elif request.object_type == "binaryOutput":
            point_obj = binary_output(
                instance=request.instance_number,
                name=request.object_name,
                description=request.description,
                presentValue=int(request.present_value),
                activeText=request.active_text,
                inactiveText=request.inactive_text,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported object type: {request.object_type}",
            )

        # Register point with device
        point_obj.add_objects_to_application(bacnet_device)

        # Track point
        if device_id not in virtual_device_points:
            virtual_device_points[device_id] = []
        virtual_device_points[device_id].append(point_obj)

        logger.info(
            f"✅ Added {request.object_type}:{request.instance_number} "
            f"to device {device_id}"
        )

        return {
            "success": True,
            "device_id": device_id,
            "point": {
                "object_type": request.object_type,
                "instance_number": request.instance_number,
                "object_name": request.object_name,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to add point: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Background Sync ====================


@sync_to_async
def get_running_devices():
    """Get devices from database (sync function)"""
    return list(VirtualBACnetDevice.objects.filter(is_running=True))


@app.post("/api/virtual-devices/sync")
async def sync_virtual_devices():
    """Sync virtual devices from Django database (background task)"""
    try:
        # Get devices marked as running from database (async-safe)
        devices_to_run = await get_running_devices()

        # Start new devices
        for device in devices_to_run:
            if device.device_id not in running_virtual_devices:
                try:
                    # Get IP based on OS or environment variable
                    bacnet_ip = get_bacnet_ip()

                    bacnet_device = BAC0.lite(
                        ip=bacnet_ip,
                        deviceId=device.device_id,
                        port=device.port,
                        localObjName=device.device_name,
                    )
                    running_virtual_devices[device.device_id] = bacnet_device
                    logger.info(
                        f"✅ Virtual device {device.device_id} started "
                        f"on port {device.port}"
                    )
                except Exception as e:
                    logger.error(
                        f"❌ Failed to start virtual device {device.device_id}: {e}"
                    )

        # Stop removed devices
        current_device_ids = set(d.device_id for d in devices_to_run)
        for device_id in list(running_virtual_devices.keys()):
            if device_id not in current_device_ids:
                running_virtual_devices[device_id].disconnect()
                del running_virtual_devices[device_id]
                logger.info(f"⏹️ Virtual device {device_id} stopped")

        return {
            "success": True,
            "running_devices": len(running_virtual_devices),
            "device_ids": list(running_virtual_devices.keys()),
        }
    except Exception as e:
        logger.error(f"❌ Virtual device sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def virtual_device_sync_loop():
    """Background loop to sync virtual devices from database"""
    logger.info("🔄 Starting virtual device sync loop (every 10 seconds)")
    while True:
        try:
            await asyncio.sleep(10)
            await sync_virtual_devices()
        except Exception as e:
            logger.error(f"❌ Virtual device sync error: {e}")


# ==================== Main Entry Point ====================


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("🚀 BACnet API Service Starting...")
    print("=" * 60)
    print()
    print("📋 Service Information:")
    print("   • API Endpoint: http://localhost:5001")
    print("   • API Documentation: http://localhost:5001/docs")
    print("   • Health Check: http://localhost:5001/api/health")
    print()
    print("🔧 Requirements:")
    print("   • PostgreSQL database running (docker-compose up db)")
    print("   • Environment variables configured (.env file)")
    print()
    print("💡 This service provides:")
    print("   • Main BACnet device (ID: 1000, Port: 47808)")
    print("   • BACnet device discovery")
    print("   • Point reading operations")
    print("   • Additional virtual device management (Port: 47809+)")
    print()
    print("⏹️  Press Ctrl+C to stop the service")
    print("=" * 60)
    print()

    uvicorn.run(app, host="0.0.0.0", port=5001, log_level="info")
