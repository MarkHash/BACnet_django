# Hybrid BACnet Implementation Plan

## Overview
Implement a simple database-communication hybrid architecture with auto-platform detection for cross-platform BACnet discovery.

## Phase 1: Foundation Setup (Day 1)

### 1.1 Add Auto-Platform Detection
```python
# bacnet_project/settings.py
import platform
import os

def detect_bacnet_backend():
    """Auto-detect the best BACnet backend for current environment"""

    # Manual override always wins
    manual_backend = os.getenv('BACNET_BACKEND')
    if manual_backend:
        print(f"🎯 Manual override: Using {manual_backend} backend")
        return manual_backend

    # Check if inside Docker container
    is_docker = (
        os.path.exists('/.dockerenv') or
        os.getenv('DOCKER_ENV')
    )

    if is_docker:
        print("🐳 Detected Docker environment: Using docker backend")
        return 'docker'

    # Check platform
    system = platform.system()

    if system == 'Windows':
        print("🪟 Detected Windows: Using native backend")
        return 'native'

    elif system in ['Linux', 'Darwin']:  # Darwin = macOS
        print(f"🐧 Detected {system}: Using docker backend")
        return 'docker'

    else:
        print(f"❓ Unknown system {system}: Defaulting to docker backend")
        return 'docker'

# Auto-detect backend
BACNET_BACKEND = detect_bacnet_backend()

# Database configuration for native access
if BACNET_BACKEND == 'native':
    # Native Windows worker connects to localhost
    DATABASES['default']['HOST'] = 'localhost'
```

### 1.2 Create Task Model
```python
# discovery/models.py (add this model)
class BACnetTask(models.Model):
    TASK_TYPES = [
        ('discover', 'Device Discovery'),
        ('collect', 'Collect Readings'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    result = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.task_type} - {self.status} ({self.created_at})"
```

### 1.3 Run Migrations
```bash
python manage.py makemigrations discovery
python manage.py migrate
```

## Phase 2: Backend Abstraction (Day 2)

### 2.1 Create Backend Base Class
```python
# discovery/backends/__init__.py
from django.conf import settings

class BACnetBackend:
    """Base class for BACnet backend implementations"""

    def discover_devices(self, mock_mode=False):
        """Discover BACnet devices on the network"""
        raise NotImplementedError

    def collect_readings(self, device_ids=None):
        """Collect readings from BACnet devices"""
        raise NotImplementedError

    def get_status(self):
        """Get backend status"""
        raise NotImplementedError

def get_bacnet_backend():
    """Factory function to get the appropriate backend"""
    if settings.BACNET_BACKEND == 'native':
        from .database_backend import DatabaseBACnetBackend
        return DatabaseBACnetBackend()
    else:
        from .docker_backend import DockerBACnetBackend
        return DockerBACnetBackend()
```

### 2.2 Implement Docker Backend (Current Behavior)
```python
# discovery/backends/docker_backend.py
from . import BACnetBackend
from discovery.tasks import discover_devices_task, collect_readings_task

class DockerBACnetBackend(BACnetBackend):
    """Backend that uses Docker containers and Celery tasks"""

    def discover_devices(self, mock_mode=False):
        """Use existing Celery task for device discovery"""
        result = discover_devices_task.delay(mock_mode=mock_mode)
        return result.get()

    def collect_readings(self, device_ids=None):
        """Use existing Celery task for reading collection"""
        result = collect_readings_task.delay()
        return result.get()

    def get_status(self):
        return {"backend": "docker", "status": "running"}
```

### 2.3 Implement Database Backend (New)
```python
# discovery/backends/database_backend.py
from datetime import datetime
from . import BACnetBackend
from discovery.models import BACnetTask

class DatabaseBACnetBackend(BACnetBackend):
    """Backend that communicates via database with native worker"""

    def discover_devices(self, mock_mode=False):
        """Create database task for device discovery"""
        task = BACnetTask.objects.create(
            task_type='discover',
            status='pending'
        )

        return {
            "task_id": task.id,
            "status": "task_created",
            "message": f"Discovery task {task.id} created. Native worker will process it."
        }

    def collect_readings(self, device_ids=None):
        """Create database task for reading collection"""
        task = BACnetTask.objects.create(
            task_type='collect',
            status='pending'
        )

        return {
            "task_id": task.id,
            "status": "task_created",
            "message": f"Collection task {task.id} created. Native worker will process it."
        }

    def get_status(self):
        recent_tasks = BACnetTask.objects.all()[:5]
        return {
            "backend": "native",
            "recent_tasks": [
                {
                    "id": task.id,
                    "type": task.task_type,
                    "status": task.status,
                    "created": task.created_at.isoformat()
                }
                for task in recent_tasks
            ]
        }
```

## Phase 3: Update Django Views (Day 3)

### 3.1 Update Discovery Views
```python
# discovery/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from .backends import get_bacnet_backend
from .models import BACnetDevice, BACnetTask

def trigger_discovery(request):
    """Trigger device discovery using appropriate backend"""
    backend = get_bacnet_backend()

    try:
        result = backend.discover_devices(mock_mode=False)

        if 'task_id' in result:
            messages.success(request, f"Discovery task {result['task_id']} started")
        else:
            messages.success(request, "Device discovery completed")

    except Exception as e:
        messages.error(request, f"Discovery failed: {e}")

    return redirect('device_list')

def device_list(request):
    """Display devices and task status"""
    devices = BACnetDevice.objects.all()
    recent_tasks = BACnetTask.objects.filter(
        task_type='discover'
    ).order_by('-created_at')[:5]

    backend = get_bacnet_backend()
    backend_status = backend.get_status()

    return render(request, 'discovery/device_list.html', {
        'devices': devices,
        'recent_tasks': recent_tasks,
        'backend_status': backend_status
    })

def task_status_api(request, task_id):
    """API endpoint for task status"""
    try:
        task = BACnetTask.objects.get(id=task_id)
        return JsonResponse({
            'id': task.id,
            'status': task.status,
            'type': task.task_type,
            'created': task.created_at.isoformat(),
            'completed': task.completed_at.isoformat() if task.completed_at else None,
            'result': task.result,
            'error': task.error_message
        })
    except BACnetTask.DoesNotExist:
        return JsonResponse({'error': 'Task not found'}, status=404)
```

### 3.2 Update Templates
```html
<!-- discovery/templates/discovery/device_list.html -->
<div class="backend-status">
    <h3>BACnet Backend Status</h3>
    <p><strong>Backend:</strong> {{ backend_status.backend }}</p>

    {% if recent_tasks %}
    <h4>Recent Tasks</h4>
    <table class="table">
        <thead>
            <tr>
                <th>ID</th>
                <th>Type</th>
                <th>Status</th>
                <th>Created</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for task in recent_tasks %}
            <tr>
                <td>{{ task.id }}</td>
                <td>{{ task.get_task_type_display }}</td>
                <td>
                    <span class="badge badge-{{ task.status|status_color }}">
                        {{ task.get_status_display }}
                    </span>
                </td>
                <td>{{ task.created_at|date:"M d, H:i" }}</td>
                <td>
                    <a href="#" onclick="checkTaskStatus({{ task.id }})">
                        Check Status
                    </a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% endif %}
</div>

<script>
function checkTaskStatus(taskId) {
    fetch(`/api/task-status/${taskId}/`)
        .then(response => response.json())
        .then(data => {
            alert(`Task ${data.id}: ${data.status}`);
            if (data.status === 'completed') {
                location.reload(); // Refresh to show new devices
            }
        });
}
</script>
```

## Phase 4: Native Windows Worker (Day 4)

### 4.1 Create Native Worker Script
```python
# bacnet_native_worker.py
"""
Native BACnet Worker for Windows
Polls database for pending tasks and executes them using native Windows networking
"""

import os
import sys
import django
import time
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bacnet_project.settings')
django.setup()

from discovery.models import BACnetTask, BACnetDevice, BACnetReading
from discovery.services import BACnetService

class NativeBACnetWorker:
    def __init__(self):
        self.running = False

    def start(self):
        """Start the worker loop"""
        print("🪟 Starting Native BACnet Worker for Windows...")
        print("📡 Using Windows host network for BACnet discovery")
        print("🗄️  Monitoring database for pending tasks...")

        self.running = True

        while self.running:
            try:
                self.process_pending_tasks()
                time.sleep(5)  # Check every 5 seconds

            except KeyboardInterrupt:
                print("\n⏹️  Stopping worker...")
                self.running = False

            except Exception as e:
                print(f"❌ Worker error: {e}")
                time.sleep(10)  # Wait longer on error

    def process_pending_tasks(self):
        """Process all pending tasks in the database"""
        pending_tasks = BACnetTask.objects.filter(status='pending')

        for task in pending_tasks:
            print(f"🔄 Processing task {task.id}: {task.task_type}")

            # Mark as running
            task.status = 'running'
            task.save()

            try:
                if task.task_type == 'discover':
                    result = self.run_discovery()
                elif task.task_type == 'collect':
                    result = self.run_collection()
                else:
                    raise ValueError(f"Unknown task type: {task.task_type}")

                # Mark as completed
                task.status = 'completed'
                task.result = result
                task.completed_at = datetime.now()
                task.save()

                print(f"✅ Task {task.id} completed: {result}")

            except Exception as e:
                # Mark as failed
                task.status = 'failed'
                task.error_message = str(e)
                task.save()

                print(f"❌ Task {task.id} failed: {e}")

    def run_discovery(self):
        """Run BACnet device discovery"""
        print("🔍 Starting BACnet device discovery on Windows network...")

        with BACnetService() as service:
            devices = service.discover_devices(mock_mode=False)

        print(f"📡 Found {len(devices)} devices on Windows network")
        return {"devices_found": len(devices), "network": "windows_host"}

    def run_collection(self):
        """Run BACnet reading collection"""
        print("📊 Starting BACnet reading collection...")

        with BACnetService() as service:
            readings = service.collect_all_readings()

        print(f"📈 Collected {len(readings)} readings")
        return {"readings_collected": len(readings)}

if __name__ == '__main__':
    worker = NativeBACnetWorker()
    worker.start()
```

### 4.2 Create Windows Batch Startup Script
```batch
@echo off
REM start_native_worker.bat
echo Starting BACnet Native Worker for Windows...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found. Please install Python.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Install required packages if needed
pip install django psycopg2 BAC0 python-dotenv

REM Start the native worker
echo Starting native worker...
python bacnet_native_worker.py

pause
```

## Phase 5: Docker Configuration Updates (Day 5)

### 5.1 Create Windows Docker Compose Override
```yaml
# docker-compose.windows.yml
# Override file for Windows native BACnet worker

services:
  # Remove bacnet-worker service for Windows
  bacnet-worker:
    deploy:
      replicas: 0  # Don't start this service on Windows

  web:
    environment:
      - BACNET_BACKEND=native  # Force native backend if needed
```

### 5.2 Update Main Docker Compose
```yaml
# docker-compose.yml (update web service)
services:
  web:
    # ... existing config
    environment:
      # Let auto-detection handle backend selection
      - DEBUG=${DEBUG}
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      # BACNET_BACKEND will be auto-detected
```

## Phase 6: Testing & Validation (Day 6)

### 6.1 Test Auto-Detection
```python
# Test in Django shell
from django.conf import settings
print(f"🔍 Auto-detected backend: {settings.BACNET_BACKEND}")

from discovery.backends import get_bacnet_backend
backend = get_bacnet_backend()
print(f"🔧 Backend class: {backend.__class__.__name__}")
print(f"📊 Backend status: {backend.get_status()}")
```

### 6.2 Test Database Communication
```python
# Test task creation
from discovery.models import BACnetTask

# Create test task
task = BACnetTask.objects.create(
    task_type='discover',
    status='pending'
)

print(f"✅ Created task {task.id}")

# Check if native worker processes it
import time
time.sleep(10)

task.refresh_from_db()
print(f"📊 Task status: {task.status}")
```

### 6.3 Cross-Platform Testing
```bash
# Linux/Mac: Should use Docker backend
docker-compose up -d
# Check logs for: "🐧 Detected Linux: Using docker backend"

# Windows: Should use native backend
docker-compose up -d
python bacnet_native_worker.py
# Check logs for: "🪟 Detected Windows: Using native backend"
```

## Deployment Instructions

### Windows Deployment
```bash
# 1. Start Docker services (auto-detects native backend)
docker-compose up -d

# 2. Start native worker
python bacnet_native_worker.py
# or
start_native_worker.bat
```

### Linux/Mac Deployment
```bash
# Just start Docker (auto-detects docker backend)
docker-compose up -d
```

## Success Criteria

✅ **Auto-Detection Works**: Platform correctly detected without manual config
✅ **Database Communication**: Tasks created in Django, processed by native worker
✅ **Cross-Platform**: Same code works on Windows, Linux, Mac
✅ **Windows Networking**: Native worker uses 192.168.1.x network
✅ **Task Monitoring**: Web interface shows task status and results
✅ **Graceful Fallback**: Manual override available via environment variable

## Timeline Summary

- **Day 1**: Foundation (auto-detection, task model)
- **Day 2**: Backend abstraction layer
- **Day 3**: Django views and templates
- **Day 4**: Native Windows worker
- **Day 5**: Docker configuration
- **Day 6**: Testing and validation

**Total effort**: ~6 days for complete implementation

This plan provides a simple, robust solution that automatically adapts to the platform while maintaining the same user experience across all environments.