# BACnet Django Application Architecture

## Overview

This application provides BACnet device discovery and monitoring capabilities through a Django web interface. The architecture supports two deployment modes to accommodate different operating system requirements for BACnet networking.

## Deployment Architectures

### 1. Separated Service Architecture (Linux/macOS)

**Best for:** Docker-based deployments on Linux/macOS where network isolation is acceptable

```
┌─────────────────────────────────────────────────────────┐
│                    Host Machine                          │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  BACnet API Service (Port 5001)                  │  │
│  │  - Runs directly on host network                 │  │
│  │  - FastAPI server                                │  │
│  │  - BAC0 library for BACnet/IP communication      │  │
│  │  - Device discovery via WhoIs broadcasts         │  │
│  │  - Point reading and value collection            │  │
│  └──────────────────────────────────────────────────┘  │
│                         ↓ HTTP (localhost:5001)         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Docker Container: Django Web App (Port 8000)    │  │
│  │  - User interface and dashboard                  │  │
│  │  - Device management                             │  │
│  │  - Communicates with BACnet API via HTTP         │  │
│  └──────────────────────────────────────────────────┘  │
│                         ↓                               │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Docker Container: PostgreSQL (Port 5432)        │  │
│  │  - Stores devices, points, readings              │  │
│  │  - Historical data                               │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Files:**
- `bacnet_api_service.py` - BACnet API service (run on host)
- `docker-compose.yml` - Docker configuration for web + db

**Why Separated?**
- Docker containers can't directly access host network for BACnet broadcasts
- BACnet/IP requires UDP broadcast packets (port 47808)
- Running BACnet service on host ensures proper network access

### 2. Integrated Service Architecture (Windows)

**Best for:** Windows development/deployment where Docker networking is limited

```
┌─────────────────────────────────────────────────────────┐
│                    Host Machine                          │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Integrated Server (Port 8000)                   │  │
│  │  ┌────────────────────────────────────────────┐  │  │
│  │  │  Django App Thread                         │  │  │
│  │  │  - Web interface & API endpoints           │  │  │
│  │  └────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────┐  │  │
│  │  │  BACnet Service (in-process)               │  │  │
│  │  │  - BAC0 library integration                │  │  │
│  │  │  - Device discovery                        │  │  │
│  │  │  - Point reading                           │  │  │
│  │  └────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────┘  │
│                         ↓                               │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Docker Container: PostgreSQL (Port 5432)        │  │
│  │  - Database only                                 │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Files:**
- `windows_integrated_server.py` - Combined Django + BACnet service
- `docker-compose.windows.yml` - Database only

**Why Integrated?**
- Simpler Windows deployment (single process)
- No need for separate FastAPI service
- Direct BAC0 integration in Django process

## Network Detection

Both architectures use OS-based network detection:

```python
def get_bacnet_ip() -> str:
    system = platform.system()
    if system == "Darwin":  # macOS
        return "192.168.1.101/24"  # Home network
    elif system == "Windows":
        return "192.168.1.5/24"    # Office network
    else:
        raise RuntimeError(f"Unsupported platform: {system}")
```

This allows automatic network configuration based on the deployment environment.

## Core Components

### Django Application Layer

**Models** (`models.py`)
- `BACnetDevice` - Discovered BACnet devices
- `BACnetPoint` - Object points (analog inputs, binary values, etc.)
- `BACnetReading` - Time-series sensor data
- `DeviceStatusHistory` - Device connectivity tracking
- `VirtualBACnetDevice` - Virtual devices for testing (Beta)

**Views** (`views.py`)
- Dashboard with device overview
- Device detail pages with real-time readings
- Virtual device management (Beta feature)

**API Endpoints** (`urls.py`)
- `/api/start-discovery/` - Discover BACnet devices
- `/api/discover-points/<device_id>/` - Discover device points
- `/api/read-values/<device_id>/` - Read all point values
- `/api/devices/status/` - Device status summary
- `/api/devices/<device_id>/trends/` - Device analytics

### BACnet Service Layer

**Service** (`services.py` or `bacnet_api_service.py`)
- BAC0 library integration
- Device discovery via WhoIs broadcasts
- Point discovery and cataloging
- Value reading with error handling
- Status monitoring

### Database Schema

```
BACnetDevice (1) ──< (N) BACnetPoint
     │                      │
     │                      │
     ├──< (N) DeviceStatusHistory
     │
     └──< (N) BACnetReading
```

## API Architecture

### REST API Endpoints

**Device Discovery:**
- `POST /api/start-discovery/` - Trigger WhoIs discovery
- `POST /api/discover-points/<device_id>/` - Discover points
- `POST /api/clear-devices/` - Clear all devices

**Data Reading:**
- `POST /api/read-values/<device_id>/` - Read all points
- `GET /api/read-point/<device_id>/<type>/<instance>/` - Read single point
- `GET /api/device-values/<device_id>/` - Get latest values

**Analytics:**
- `GET /api/devices/status/` - Device status summary
- `GET /api/devices/<device_id>/analytics/trends/` - Trends data

**Virtual Devices (Beta):**
- `GET /virtual-devices/` - List virtual devices
- `POST /virtual-devices/create/` - Create virtual device
- `POST /api/virtual-devices/<device_id>/delete/` - Delete virtual device

## Testing

### JavaScript Tests (Jest)
- 16 passing tests for device detail page
- Coverage for DOM manipulation and API calls
- Run: `npm test`

### Python Tests (Django)
- Unit tests for models, views, utils
- Integration tests
- Run: `python manage.py test discovery`

## Technology Stack

**Backend:**
- Django 5.2+ - Web framework
- PostgreSQL 12+ - Database
- BAC0 23.07.03+ - BACnet protocol library
- FastAPI - API service (separated mode)

**Frontend:**
- Bootstrap 5 - UI framework
- Vanilla JavaScript - Interactivity
- Django Templates - Server-side rendering

**DevOps:**
- Docker - Containerization
- docker-compose - Multi-container orchestration
- Pre-commit hooks - Code quality (black, flake8, isort)

## Key Design Decisions

### 1. Why Separated Architecture for Docker?
Docker's network isolation prevents BACnet UDP broadcasts from reaching the host network. Running the BACnet service on the host ensures proper device discovery.

### 2. Why Integrated Architecture for Windows?
Simplifies deployment and avoids FastAPI dependency. Windows development typically doesn't use Docker for the application layer.

### 3. Why BAC0 Library?
- Pure Python implementation
- Simple API for BACnet/IP operations
- Active community support
- Cross-platform compatibility

### 4. Why PostgreSQL?
- Robust time-series data handling
- Better performance for large datasets
- Production-ready features (JSONB, indexing)

## Future Improvements

### Enhanced Virtual Device Architecture (High Priority)

**Current Limitation:**
The current integrated architecture makes it difficult to create fully functional virtual BACnet devices that are discoverable by other BACnet clients on the network.

**Proposed Architecture:**

```
┌─────────────────────────────────────────────────────────┐
│                    Host Machine                          │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  BACnet API Service (Port 5001) - FastAPI        │  │
│  │  ┌────────────────────────────────────────────┐  │  │
│  │  │  Async Virtual Device Manager              │  │  │
│  │  │  ├── Virtual Device 1000 (async server)    │  │  │
│  │  │  ├── Virtual Device 1001 (async server)    │  │  │
│  │  │  └── Virtual Device 1002 (async server)    │  │  │
│  │  └────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────┐  │  │
│  │  │  BACnet Client (Discovery & Reading)       │  │  │
│  │  └────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────┘  │
│                 ↑ HTTP API                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Docker: Django Web App (Port 8000)              │  │
│  │  - User interface                                │  │
│  │  - HTTP client to BACnet API                     │  │
│  │  - Database operations                           │  │
│  └──────────────────────────────────────────────────┘  │
│                 ↓                                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Docker: PostgreSQL                              │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Why This Architecture is Needed:**

**Problem with Current Approach:**
- Django's WSGI is synchronous - blocks during virtual device operations
- Creating multiple virtual devices requires async event loops for concurrent UDP listeners
- Each virtual device needs to listen on port 47808 and respond to BACnet requests
- Mixing web requests with BACnet network operations creates complexity

**Solution with Separated Architecture:**
- FastAPI provides native async/await support
- BACnet API runs on host with direct network access
- Virtual devices can run concurrently without blocking web app
- Each virtual device acts as independent BACnet server (discoverable via WhoIs)
- Django simplified to just UI + database + HTTP client calls

**Benefits:**
- ✅ **True async support**: Manage 100+ virtual devices concurrently
- ✅ **Network discoverability**: Virtual devices respond to WhoIs broadcasts from real BACnet clients
- ✅ **Clean separation**: BACnet networking logic isolated from web application
- ✅ **Scalability**: Can handle complex testing scenarios with many devices
- ✅ **Platform consistency**: Same architecture on Windows, macOS, Linux

**Implementation Requirements:**
- FastAPI service with async virtual device manager
- BAC0.VirtualDevice instances running as async servers
- Django HTTP client to communicate with BACnet API
- Docker configuration with `host.docker.internal` for API access

**Estimated Effort:** 2-3 weeks

**Reference:** The `feat/bacnet-api-service` branch explored this architecture but became overly complex. A simplified async-only-where-needed approach would be more maintainable.

---

### Other Planned Enhancements

**Automated Reading Collection:**
- Scheduled periodic data collection (Celery + Redis)
- Configurable intervals per device
- Background task processing

**Advanced Analytics:**
- Time-series visualization (Chart.js/Plotly)
- Anomaly detection for unusual readings
- Data export (CSV/Excel)
- Custom dashboards

**Real-time Updates:**
- WebSocket support (Django Channels)
- Live sensor value updates without page refresh
- Instant device status notifications

**Device-Specific Collection:**
- Implement TODO in `collect_readings.py:25`
- Selective reading from specific devices
- Optimized data collection strategies

**Additional Features:**
- User authentication and role-based permissions
- Device groups and organization
- Alerting and notifications
- BACnet write operations (control setpoints)
- Multi-network support

## Security Considerations

- Environment variables for sensitive config
- Django security middleware enabled
- Database credentials in `.env` (gitignored)
- Admin interface protected by authentication

---

**Architecture Documentation**
Last Updated: October 2024
Version: 1.0 (Simplified Core)
