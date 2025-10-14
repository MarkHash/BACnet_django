# Simple Hybrid Architecture - Database Communication

## Core Principle: Shared Database Only

Both Docker containers and Windows native service communicate through the PostgreSQL database. No HTTP APIs, no extra services.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                Docker Services                          │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ Web (Django)    │  │ PostgreSQL DB   │              │
│  │ - Web Interface │◄─┤ - Shared Models │◄─┐           │
│  │ - Trigger Tasks │  │ - Device Data   │  │           │
│  │ - View Results  │  │ - Readings      │  │           │
│  └─────────────────┘  └─────────────────┘  │           │
└─────────────────────────────────────────────┼───────────┘
                                              │
┌─────────────────────────────────────────────┼───────────┐
│                Windows Host                 │           │
│  ┌─────────────────────────────────────────┐│           │
│  │        Native BACnet Worker             ││           │
│  │  ┌─────────────────────────────────────┐││           │
│  │  │ Simple Python Script               │├┘           │
│  │  │ - Connect to PostgreSQL            ││             │
│  │  │ - Run BACnet Discovery             ││             │
│  │  │ - Write Results to DB              ││             │
│  │  │ - Use Windows Network (192.168.1.x)││             │
│  │  └─────────────────────────────────────┘│             │
│  └─────────────────────────────────────────┘             │
└───────────────────────────────────────────────────────────┘
```

## Implementation

### 1. Shared Database Models (No Changes)
Current Django models work for both Docker and native:
```python
# discovery/models.py (unchanged)
class BACnetDevice(models.Model):
    # ... existing fields

class BACnetReading(models.Model):
    # ... existing fields
```

### 2. Simple Task Triggering
Instead of Celery tasks, use database flags:

```python
# discovery/models.py (add this)
class BACnetTask(models.Model):
    TASK_TYPES = [
        ('discover', 'Device Discovery'),
        ('collect', 'Collect Readings'),
    ]

    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    status = models.CharField(max_length=20, default='pending')  # pending, running, completed, failed
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    result = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)
```

### 3. Django Web - Task Triggering
```python
# discovery/views.py
def trigger_discovery(request):
    # Create task record
    task = BACnetTask.objects.create(
        task_type='discover',
        status='pending'
    )

    messages.success(request, f"Discovery task {task.id} started")
    return redirect('device_list')

def device_list(request):
    devices = BACnetDevice.objects.all()

    # Show task status
    recent_tasks = BACnetTask.objects.filter(
        task_type='discover'
    ).order_by('-created_at')[:5]

    return render(request, 'devices.html', {
        'devices': devices,
        'recent_tasks': recent_tasks
    })
```

### 4. Windows Native Worker (Simple Script)
```python
# bacnet_native_worker.py
import os
import django
import time
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bacnet_project.settings')
django.setup()

from discovery.models import BACnetTask, BACnetDevice, BACnetReading
from discovery.services import BACnetService

def process_pending_tasks():
    pending_tasks = BACnetTask.objects.filter(status='pending')

    for task in pending_tasks:
        print(f"Processing task {task.id}: {task.task_type}")

        # Mark as running
        task.status = 'running'
        task.save()

        try:
            if task.task_type == 'discover':
                result = run_discovery()
            elif task.task_type == 'collect':
                result = run_collection()

            # Mark as completed
            task.status = 'completed'
            task.result = result
            task.completed_at = datetime.now()
            task.save()

            print(f"Task {task.id} completed: {result}")

        except Exception as e:
            # Mark as failed
            task.status = 'failed'
            task.error_message = str(e)
            task.save()

            print(f"Task {task.id} failed: {e}")

def run_discovery():
    with BACnetService() as service:
        devices = service.discover_devices(mock_mode=False)
        print(f"Found {len(devices)} devices on Windows network")
        return {"devices_found": len(devices)}

def run_collection():
    with BACnetService() as service:
        readings = service.collect_all_readings()
        return {"readings_collected": len(readings)}

if __name__ == '__main__':
    print("Starting BACnet Native Worker...")
    print("Monitoring database for pending tasks...")

    while True:
        try:
            process_pending_tasks()
            time.sleep(5)  # Check every 5 seconds
        except KeyboardInterrupt:
            print("Stopping worker...")
            break
        except Exception as e:
            print(f"Worker error: {e}")
            time.sleep(10)  # Wait longer on error
```

### 5. Database Configuration for Native Access
```python
# settings.py (add Windows database access)
import platform

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        # Windows native connects to localhost, Docker connects to 'db'
        'HOST': 'localhost' if platform.system() == 'Windows' else os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}
```

## Deployment Instructions

### Windows Deployment
```bash
# 1. Start Docker services (without bacnet-worker)
docker-compose -f docker-compose.yml -f docker-compose.windows.yml up -d

# 2. Install Python dependencies on Windows
pip install django psycopg2 BAC0

# 3. Run native worker
python bacnet_native_worker.py
```

### Linux/Mac Deployment
```bash
# Use existing setup (no changes needed)
docker-compose up -d
```

## Benefits of Database Communication

### ✅ Simplicity
- **Single communication channel**: Database only
- **No network complexity**: No HTTP, ports, timeouts
- **Existing infrastructure**: Uses PostgreSQL already running

### ✅ Reliability
- **Database transactions**: ACID compliance
- **Django ORM**: Handles connections, retries automatically
- **No HTTP failures**: Network requests eliminated

### ✅ Monitoring
- **Task history**: All tasks stored in database
- **Status tracking**: Pending, running, completed, failed
- **Error logging**: Exception details in database
- **Web interface**: View task status in Django admin

### ✅ Development
- **Same models**: No duplicate code
- **Easy testing**: Just check database state
- **Django admin**: Built-in task management interface

## Migration from Current Setup

### Phase 1: Add Task Model
```bash
# Add BACnetTask model
python manage.py makemigrations
python manage.py migrate
```

### Phase 2: Update Views
Replace Celery task calls with database task creation

### Phase 3: Test Native Worker
Run the simple Python script and verify it processes tasks

### Phase 4: Remove Celery (Optional)
Once native worker proven, can remove Celery complexity

This approach eliminates all the HTTP API complexity while providing the same functionality!