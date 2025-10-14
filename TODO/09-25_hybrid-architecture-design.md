# Hybrid BACnet Architecture Design

## Problem Statement
- **Windows**: Docker cannot access host network (192.168.1.x) for BACnet discovery
- **Linux/Mac**: Docker host networking works perfectly
- **Web Container**: Needs to trigger device discovery regardless of platform

## Solution: Platform-Adaptive Hybrid Architecture

### Core Principle
Keep the **interface consistent** while adapting the **implementation** per platform.

## Architecture Components

### 1. Universal Components (All Platforms)
```
┌─────────────────────────────────────────────────────────┐
│                Docker Services                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────┐ │
│  │ Web (Django)    │  │ PostgreSQL DB   │  │ Redis   │ │
│  │ - REST API      │  │ - Device Data   │  │ - Cache │ │
│  │ - Web UI        │  │ - Readings      │  │ - Tasks │ │
│  │ - Device Mgmt   │  │ - Analytics     │  │         │ │
│  └─────────────────┘  └─────────────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 2. Platform-Specific BACnet Layer

#### Windows Implementation
```
┌─────────────────────────────────────────────────────────┐
│                Windows Host                             │
│  ┌─────────────────────────────────────────────────────┐│
│  │            BACnet Native Service                    ││
│  │  ┌─────────────────┐  ┌─────────────────────────────┐││
│  │  │ HTTP API Server │  │ BACnet Discovery Engine     │││
│  │  │ - /discover     │  │ - Uses 192.168.1.x network  │││
│  │  │ - /collect      │  │ - BAC0 library              │││
│  │  │ - /status       │  │ - Device communication      │││
│  │  └─────────────────┘  └─────────────────────────────┘││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

#### Linux/Mac Implementation
```
┌─────────────────────────────────────────────────────────┐
│                Docker Services                          │
│  ┌─────────────────────────────────────────────────────┐│
│  │              BACnet Worker                          ││
│  │  ┌─────────────────┐  ┌─────────────────────────────┐││
│  │  │ Celery Worker   │  │ BACnet Discovery Engine     │││
│  │  │ - Task Queue    │  │ - Uses host network         │││
│  │  │ - Job Processing│  │ - BAC0 library              │││
│  │  │ - Results       │  │ - Device communication      │││
│  │  └─────────────────┘  └─────────────────────────────┘││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

## Implementation Strategy

### 1. Abstraction Layer in Django

```python
# discovery/backends/__init__.py
from django.conf import settings
from .docker_backend import DockerBACnetBackend
from .native_backend import NativeBACnetBackend

def get_bacnet_backend():
    if settings.BACNET_BACKEND == 'native':
        return NativeBACnetBackend()
    else:
        return DockerBACnetBackend()

# discovery/backends/base.py
class BACnetBackend:
    def discover_devices(self, mock_mode=False):
        raise NotImplementedError

    def collect_readings(self, device_ids=None):
        raise NotImplementedError

    def get_status(self):
        raise NotImplementedError
```

### 2. Docker Backend (Linux/Mac)

```python
# discovery/backends/docker_backend.py
from celery import current_app
from .base import BACnetBackend

class DockerBACnetBackend(BACnetBackend):
    def discover_devices(self, mock_mode=False):
        # Use existing Celery task
        from discovery.tasks import discover_devices_task
        result = discover_devices_task.delay(mock_mode=mock_mode)
        return result.get()

    def collect_readings(self, device_ids=None):
        from discovery.tasks import collect_readings_task
        result = collect_readings_task.delay()
        return result.get()
```

### 3. Native Backend (Windows)

```python
# discovery/backends/native_backend.py
import requests
from django.conf import settings
from .base import BACnetBackend

class NativeBACnetBackend(BACnetBackend):
    def __init__(self):
        self.api_base = settings.NATIVE_BACNET_API_URL

    def discover_devices(self, mock_mode=False):
        response = requests.post(f"{self.api_base}/discover",
                               json={"mock_mode": mock_mode})
        return response.json()

    def collect_readings(self, device_ids=None):
        response = requests.post(f"{self.api_base}/collect",
                               json={"device_ids": device_ids})
        return response.json()
```

### 4. Native Windows Service

```python
# bacnet_native_service.py
from flask import Flask, request, jsonify
from discovery.services import BACnetService
import threading
import time

app = Flask(__name__)

@app.route('/discover', methods=['POST'])
def discover_devices():
    data = request.get_json()
    mock_mode = data.get('mock_mode', False)

    with BACnetService() as service:
        devices = service.discover_devices(mock_mode=mock_mode)
        return jsonify(devices)

@app.route('/collect', methods=['POST'])
def collect_readings():
    data = request.get_json()
    device_ids = data.get('device_ids')

    with BACnetService() as service:
        readings = service.collect_all_readings()
        return jsonify(readings)

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({"status": "running", "platform": "windows"})

if __name__ == '__main__':
    app.run(host='localhost', port=5001)
```

## Configuration Management

### Platform Detection

```python
# settings.py
import platform
import os

# Auto-detect platform and set backend
if platform.system() == 'Windows' and not os.getenv('DOCKER_ENV'):
    BACNET_BACKEND = 'native'
    NATIVE_BACNET_API_URL = 'http://localhost:5001'
else:
    BACNET_BACKEND = 'docker'

# Or manual override
BACNET_BACKEND = os.getenv('BACNET_BACKEND', BACNET_BACKEND)
```

### Docker Compose Configurations

```yaml
# docker-compose.yml (base)
services:
  web:
    environment:
      - BACNET_BACKEND=${BACNET_BACKEND:-docker}
      - NATIVE_BACNET_API_URL=${NATIVE_BACNET_API_URL:-}

# docker-compose.override.yml (Linux/Mac)
services:
  bacnet-worker:
    # Include BACnet worker for Linux/Mac

# docker-compose.windows.yml
services:
  # No bacnet-worker service
  web:
    environment:
      - BACNET_BACKEND=native
      - NATIVE_BACNET_API_URL=http://host.docker.internal:5001
```

## Benefits of This Approach

### ✅ Advantages
1. **Unified Interface**: Web container code doesn't change between platforms
2. **Platform Optimization**: Native Windows networking, containerized Linux/Mac
3. **Development Flexibility**: Easy to switch between backends
4. **Production Ready**: Optimal performance on each platform
5. **Gradual Migration**: Can implement platform by platform

### ⚠️ Considerations
1. **Complexity**: Two different backends to maintain
2. **Testing**: Need to test both implementations
3. **Deployment**: Platform-specific deployment procedures
4. **Debugging**: Different troubleshooting approaches per platform

## Migration Strategy

### Phase 1: Abstraction Layer
1. Create backend abstraction in Django
2. Implement Docker backend (current working solution)
3. Test with existing setup

### Phase 2: Native Windows Backend
1. Create Windows native service
2. Implement HTTP API
3. Test communication between Docker and native service

### Phase 3: Platform Detection
1. Add automatic platform detection
2. Implement configuration switching
3. Test cross-platform compatibility

### Phase 4: Production Deployment
1. Create platform-specific deployment guides
2. Implement monitoring for both backends
3. Performance optimization per platform

## Example Usage

```python
# In Django views or tasks - platform agnostic
from discovery.backends import get_bacnet_backend

def trigger_discovery():
    backend = get_bacnet_backend()
    result = backend.discover_devices(mock_mode=False)
    return result
```

This approach provides the best of both worlds: containerized development with native networking where needed, while maintaining a consistent interface across platforms.