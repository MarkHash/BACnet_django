# Virtual BACnet Device - MVP Implementation Guide

**Status:** POC Validated ✅ (Device ID 999 successfully created)
**Next:** Django Integration
**Timeline:** Days 2-6 (6 working days remaining)

---

## 🎯 MVP Architecture Overview

```
User (Web Browser)
    ↓
Django Views/Forms (Create virtual device)
    ↓
VirtualBACnetDevice Model (Database)
    ↓
VirtualDeviceService (BAC0 wrapper)
    ↓
BAC0.lite(deviceId=X) (Running in background)
    ↓
Network (Discoverable BACnet device)
```

---

## 📋 Step-by-Step Implementation Plan

### **STEP 1: Django Model** (Day 2-3, ~2 hours)

**File:** `discovery/models.py`

**Add this model:**

```python
class VirtualBACnetDevice(models.Model):
    """Virtual BACnet devices created by the server"""

    # Core device info
    device_id = models.IntegerField(
        unique=True,
        help_text="BACnet device instance number (must be unique)"
    )
    device_name = models.CharField(
        max_length=200,
        help_text="Human-readable device name"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of this virtual device"
    )

    # Network configuration
    port = models.IntegerField(
        default=47808,
        help_text="BACnet UDP port (default 47808)"
    )

    # Status tracking
    is_running = models.BooleanField(
        default=False,
        help_text="Whether the virtual device is currently running"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['device_id']
        verbose_name = "Virtual BACnet Device"
        verbose_name_plural = "Virtual BACnet Devices"

    def __str__(self):
        return f"Virtual Device {self.device_id} - {self.device_name}"
```

**Tasks:**
1. ✅ Add model to `discovery/models.py`
2. ✅ Create migration: `python manage.py makemigrations`
3. ✅ Apply migration: `python manage.py migrate`
4. ✅ Register in admin (optional): `discovery/admin.py`

**Admin Registration (optional):**
```python
# In discovery/admin.py
from .models import VirtualBACnetDevice

@admin.register(VirtualBACnetDevice)
class VirtualBACnetDeviceAdmin(admin.ModelAdmin):
    list_display = ['device_id', 'device_name', 'port', 'is_running', 'created_at']
    list_filter = ['is_running']
    search_fields = ['device_id', 'device_name']
```

**Validation:**
- ✅ Run Django shell: `python manage.py shell`
- ✅ Test: `from discovery.models import VirtualBACnetDevice`
- ✅ Create test record: `VirtualBACnetDevice.objects.create(device_id=999, device_name="Test Device")`

---

### **STEP 2: Management Command** (Day 3, ~2-3 hours)

**File:** `discovery/management/commands/run_virtual_devices.py`

**Purpose:** Keep BAC0 instances running in background

**Directory structure:**
```
discovery/
├── management/
│   ├── __init__.py
│   └── commands/
│       ├── __init__.py
│       └── run_virtual_devices.py
```

**Implementation:**

```python
"""
Management command to run virtual BACnet device server

Usage:
    python manage.py run_virtual_devices
"""

import signal
import sys
import time
from django.core.management.base import BaseCommand
import BAC0
from discovery.models import VirtualBACnetDevice


class Command(BaseCommand):
    help = 'Run virtual BACnet device server'

    def __init__(self):
        super().__init__()
        self.running_devices = {}  # {device_id: bacnet_instance}
        self.shutdown = False

    def handle(self, *args, **options):
        # Setup graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        self.stdout.write(self.style.SUCCESS('Starting Virtual BACnet Device Server...'))

        # Start all devices marked as should be running
        self.start_all_devices()

        # Keep running
        try:
            while not self.shutdown:
                time.sleep(5)  # Check every 5 seconds
                self.check_device_states()
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()

    def start_all_devices(self):
        """Start all virtual devices from database"""
        devices = VirtualBACnetDevice.objects.filter(is_running=True)

        for device in devices:
            self.start_device(device)

    def start_device(self, device):
        """Start a single virtual device"""
        try:
            self.stdout.write(f'Starting device {device.device_id}...')

            bacnet = BAC0.lite(
                deviceId=device.device_id,
                port=device.port
            )

            self.running_devices[device.device_id] = bacnet
            self.stdout.write(self.style.SUCCESS(
                f'✓ Device {device.device_id} started on port {device.port}'
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'✗ Failed to start device {device.device_id}: {e}'
            ))
            device.is_running = False
            device.save()

    def check_device_states(self):
        """Check if new devices should be started or stopped"""
        # Get devices that should be running from DB
        should_run = set(
            VirtualBACnetDevice.objects.filter(is_running=True)
            .values_list('device_id', flat=True)
        )

        currently_running = set(self.running_devices.keys())

        # Start new devices
        to_start = should_run - currently_running
        for device_id in to_start:
            device = VirtualBACnetDevice.objects.get(device_id=device_id)
            self.start_device(device)

        # Stop removed devices
        to_stop = currently_running - should_run
        for device_id in to_stop:
            self.stop_device(device_id)

    def stop_device(self, device_id):
        """Stop a single virtual device"""
        if device_id in self.running_devices:
            self.stdout.write(f'Stopping device {device_id}...')
            self.running_devices[device_id].disconnect()
            del self.running_devices[device_id]
            self.stdout.write(self.style.SUCCESS(f'✓ Device {device_id} stopped'))

    def cleanup(self):
        """Stop all running devices"""
        self.stdout.write(self.style.WARNING('\nShutting down...'))

        for device_id in list(self.running_devices.keys()):
            self.stop_device(device_id)

        self.stdout.write(self.style.SUCCESS('✓ All devices stopped'))

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.shutdown = True
```

**Tasks:**
1. ✅ Create directory structure
2. ✅ Create `__init__.py` files
3. ✅ Create `run_virtual_devices.py`
4. ✅ Test: `python manage.py run_virtual_devices`

**Testing:**
```bash
# Terminal 1: Start server
python manage.py run_virtual_devices

# Terminal 2: Django shell - create device
python manage.py shell
>>> from discovery.models import VirtualBACnetDevice
>>> VirtualBACnetDevice.objects.create(device_id=999, device_name="Test", is_running=True)

# Check Terminal 1 - device should auto-start within 5 seconds
```

---

### **STEP 3: Service Layer** (Day 4, ~2-3 hours)

**File:** `discovery/virtual_device_service.py` (NEW)

**Purpose:** Manage virtual device lifecycle from Django views

```python
"""
Virtual Device Service Layer

Handles creation, deletion, and management of virtual BACnet devices
"""

import logging
import BAC0
from .models import VirtualBACnetDevice

logger = logging.getLogger(__name__)


class VirtualDeviceService:
    """Service for managing virtual BACnet devices"""

    @staticmethod
    def create_virtual_device(device_id, device_name, description="", port=47808):
        """
        Create a virtual device in database

        Args:
            device_id (int): Unique BACnet device ID
            device_name (str): Human-readable name
            description (str): Optional description
            port (int): BACnet port (default 47808)

        Returns:
            VirtualBACnetDevice: Created device instance

        Raises:
            ValueError: If device_id already exists
        """
        # Check if device_id already exists
        if VirtualBACnetDevice.objects.filter(device_id=device_id).exists():
            raise ValueError(f"Device ID {device_id} already exists")

        # Create device in database
        device = VirtualBACnetDevice.objects.create(
            device_id=device_id,
            device_name=device_name,
            description=description,
            port=port,
            is_running=True  # Mark as should be running
        )

        logger.info(f"Virtual device created: {device_id} - {device_name}")
        return device

    @staticmethod
    def delete_virtual_device(device_id):
        """
        Delete a virtual device

        Args:
            device_id (int): Device ID to delete

        Returns:
            bool: True if deleted, False if not found
        """
        try:
            device = VirtualBACnetDevice.objects.get(device_id=device_id)
            device.is_running = False  # Signal management command to stop
            device.save()
            device.delete()

            logger.info(f"Virtual device deleted: {device_id}")
            return True
        except VirtualBACnetDevice.DoesNotExist:
            logger.warning(f"Device {device_id} not found")
            return False

    @staticmethod
    def start_virtual_device(device_id):
        """
        Mark device as should be running
        Management command will pick it up within 5 seconds

        Args:
            device_id (int): Device ID to start

        Returns:
            bool: True if started, False if not found
        """
        try:
            device = VirtualBACnetDevice.objects.get(device_id=device_id)
            device.is_running = True
            device.save()
            logger.info(f"Virtual device marked for start: {device_id}")
            return True
        except VirtualBACnetDevice.DoesNotExist:
            return False

    @staticmethod
    def stop_virtual_device(device_id):
        """
        Mark device as should be stopped

        Args:
            device_id (int): Device ID to stop

        Returns:
            bool: True if stopped, False if not found
        """
        try:
            device = VirtualBACnetDevice.objects.get(device_id=device_id)
            device.is_running = False
            device.save()
            logger.info(f"Virtual device marked for stop: {device_id}")
            return True
        except VirtualBACnetDevice.DoesNotExist:
            return False

    @staticmethod
    def get_all_devices():
        """Get all virtual devices"""
        return VirtualBACnetDevice.objects.all().order_by('device_id')

    @staticmethod
    def get_running_devices():
        """Get all running virtual devices"""
        return VirtualBACnetDevice.objects.filter(is_running=True)
```

**Tasks:**
1. ✅ Create `discovery/virtual_device_service.py`
2. ✅ Test in Django shell:

```python
from discovery.virtual_device_service import VirtualDeviceService

# Create device
device = VirtualDeviceService.create_virtual_device(
    device_id=1001,
    device_name="Temperature Sensor Simulator"
)

# List devices
devices = VirtualDeviceService.get_all_devices()
```

---

### **STEP 4: Web Forms** (Day 4, ~1 hour)

**File:** `discovery/forms.py` (NEW)

```python
"""
Forms for virtual device management
"""

from django import forms
from .models import VirtualBACnetDevice


class VirtualDeviceCreateForm(forms.ModelForm):
    """Form for creating virtual BACnet devices"""

    class Meta:
        model = VirtualBACnetDevice
        fields = ['device_id', 'device_name', 'description', 'port']
        widgets = {
            'device_id': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 999',
                'min': 0,
                'max': 4194303  # BACnet max device ID
            }),
            'device_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Virtual Temperature Sensor'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional description...'
            }),
            'port': forms.NumberInput(attrs={
                'class': 'form-control',
                'value': 47808,
                'min': 1024,
                'max': 65535
            }),
        }
        help_texts = {
            'device_id': 'Unique BACnet device ID (0-4194303)',
            'device_name': 'Human-readable name for this virtual device',
            'port': 'BACnet UDP port (default 47808, use 47809+ for additional devices)'
        }

    def clean_device_id(self):
        """Validate device_id is unique"""
        device_id = self.cleaned_data['device_id']

        if VirtualBACnetDevice.objects.filter(device_id=device_id).exists():
            raise forms.ValidationError(
                f"Device ID {device_id} already exists. Please choose a different ID."
            )

        if device_id < 0 or device_id > 4194303:
            raise forms.ValidationError(
                "Device ID must be between 0 and 4194303"
            )

        return device_id

    def clean_port(self):
        """Validate port number"""
        port = self.cleaned_data['port']

        if port < 1024 or port > 65535:
            raise forms.ValidationError(
                "Port must be between 1024 and 65535"
            )

        return port
```

**Tasks:**
1. ✅ Create `discovery/forms.py`
2. ✅ Add validation logic
3. ✅ Test form validation in Django shell

---

### **STEP 5: Views** (Day 5, ~2-3 hours)

**File:** `discovery/views.py` (UPDATE)

**Add these views:**

```python
# Add these imports at the top
from .forms import VirtualDeviceCreateForm
from .virtual_device_service import VirtualDeviceService
from django.contrib import messages
from django.shortcuts import redirect

# Add these view functions

def virtual_device_list(request: HttpRequest) -> HttpResponse:
    """List all virtual devices"""
    devices = VirtualDeviceService.get_all_devices()

    context = {
        'virtual_devices': devices,
        'total_devices': devices.count(),
        'running_devices': devices.filter(is_running=True).count(),
    }

    return render(request, 'discovery/virtual_device_list.html', context)


def virtual_device_create(request: HttpRequest) -> HttpResponse:
    """Create new virtual device"""
    if request.method == 'POST':
        form = VirtualDeviceCreateForm(request.POST)
        if form.is_valid():
            try:
                device = VirtualDeviceService.create_virtual_device(
                    device_id=form.cleaned_data['device_id'],
                    device_name=form.cleaned_data['device_name'],
                    description=form.cleaned_data.get('description', ''),
                    port=form.cleaned_data.get('port', 47808)
                )

                messages.success(
                    request,
                    f'Virtual device {device.device_id} created successfully! '
                    f'It will start within 5 seconds if the server is running.'
                )
                return redirect('discovery:virtual_device_list')

            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = VirtualDeviceCreateForm()

    context = {'form': form}
    return render(request, 'discovery/virtual_device_create.html', context)


@csrf_exempt
def virtual_device_delete(request: HttpRequest, device_id: int) -> JsonResponse:
    """Delete virtual device"""
    if request.method == 'POST':
        success = VirtualDeviceService.delete_virtual_device(device_id)

        if success:
            return JsonResponse({
                'success': True,
                'message': f'Virtual device {device_id} deleted successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': f'Virtual device {device_id} not found'
            }, status=404)

    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=400)
```

**Tasks:**
1. ✅ Add imports
2. ✅ Add view functions
3. ✅ Test views work (even without templates yet)

---

### **STEP 6: URL Routing** (Day 5, ~15 minutes)

**File:** `discovery/urls.py` (UPDATE)

**Add these URL patterns:**

```python
# Add these patterns to urlpatterns list

# Virtual device management
path('virtual-devices/', views.virtual_device_list, name='virtual_device_list'),
path('virtual-devices/create/', views.virtual_device_create, name='virtual_device_create'),
path('api/virtual-devices/<int:device_id>/delete/', views.virtual_device_delete, name='virtual_device_delete'),
```

**Full context (where to add):**
```python
urlpatterns = [
    # ... existing patterns ...

    # Virtual device management (ADD THESE)
    path('virtual-devices/', views.virtual_device_list, name='virtual_device_list'),
    path('virtual-devices/create/', views.virtual_device_create, name='virtual_device_create'),
    path('api/virtual-devices/<int:device_id>/delete/', views.virtual_device_delete, name='virtual_device_delete'),
]
```

---

### **STEP 7: Templates** (Day 5-6, ~3 hours)

**File 1:** `discovery/templates/discovery/virtual_device_list.html`

```html
{% extends 'discovery/base.html' %}

{% block title %}Virtual BACnet Devices{% endblock %}

{% block content %}
<div class="row mb-4">
    <div class="col">
        <h1>Virtual BACnet Devices</h1>
        <p class="text-muted">Create and manage virtual BACnet devices on your network</p>
    </div>
</div>

<div class="row mb-4">
    <div class="col-md-6">
        <div class="card bg-primary text-white">
            <div class="card-body text-center">
                <h3 class="card-title">{{ total_devices }}</h3>
                <p class="card-text">Total Virtual Devices</p>
            </div>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card bg-success text-white">
            <div class="card-body text-center">
                <h3 class="card-title">{{ running_devices }}</h3>
                <p class="card-text">Running Devices</p>
            </div>
        </div>
    </div>
</div>

<div class="row mb-4">
    <div class="col">
        <a href="{% url 'discovery:virtual_device_create' %}" class="btn btn-primary btn-lg">
            ➕ Create Virtual Device
        </a>
        <a href="{% url 'discovery:dashboard' %}" class="btn btn-secondary btn-lg">
            ← Back to Dashboard
        </a>
    </div>
</div>

<div class="row">
    <div class="col">
        <div class="card">
            <div class="card-header">
                <h5>Virtual Devices</h5>
            </div>
            <div class="card-body">
                {% if virtual_devices %}
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>Device ID</th>
                                    <th>Device Name</th>
                                    <th>Port</th>
                                    <th>Status</th>
                                    <th>Created</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for device in virtual_devices %}
                                <tr>
                                    <td><strong>{{ device.device_id }}</strong></td>
                                    <td>{{ device.device_name }}</td>
                                    <td>{{ device.port }}</td>
                                    <td>
                                        {% if device.is_running %}
                                            <span class="badge bg-success">Running</span>
                                        {% else %}
                                            <span class="badge bg-secondary">Stopped</span>
                                        {% endif %}
                                    </td>
                                    <td>{{ device.created_at|date:"M d, Y H:i" }}</td>
                                    <td>
                                        <button class="btn btn-sm btn-danger delete-device-btn"
                                                data-device-id="{{ device.device_id }}"
                                                data-device-name="{{ device.device_name }}">
                                            🗑️ Delete
                                        </button>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                {% else %}
                    <div class="text-center py-5">
                        <h5 class="text-muted">No virtual devices created yet</h5>
                        <p class="text-muted">Create your first virtual BACnet device to get started</p>
                        <a href="{% url 'discovery:virtual_device_create' %}" class="btn btn-primary">
                            ➕ Create Virtual Device
                        </a>
                    </div>
                {% endif %}
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block javascript %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.delete-device-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const deviceId = this.dataset.deviceId;
            const deviceName = this.dataset.deviceName;

            if (confirm(`Are you sure you want to delete virtual device ${deviceId} (${deviceName})?`)) {
                fetch(`/api/virtual-devices/${deviceId}/delete/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(data.message);
                        location.reload();
                    } else {
                        alert('Error: ' + data.message);
                    }
                })
                .catch(error => {
                    alert('Error deleting device: ' + error);
                });
            }
        });
    });
});
</script>
{% endblock %}
```

**File 2:** `discovery/templates/discovery/virtual_device_create.html`

```html
{% extends 'discovery/base.html' %}

{% block title %}Create Virtual Device{% endblock %}

{% block content %}
<div class="row mb-4">
    <div class="col">
        <h1>Create Virtual BACnet Device</h1>
        <p class="text-muted">Create a virtual BACnet device that will be discoverable on your network</p>
    </div>
</div>

<div class="row">
    <div class="col-md-8">
        <div class="card">
            <div class="card-header">
                <h5>Device Information</h5>
            </div>
            <div class="card-body">
                <form method="post">
                    {% csrf_token %}

                    {% if messages %}
                        {% for message in messages %}
                        <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                        {% endfor %}
                    {% endif %}

                    <div class="mb-3">
                        <label for="{{ form.device_id.id_for_label }}" class="form-label">
                            Device ID <span class="text-danger">*</span>
                        </label>
                        {{ form.device_id }}
                        <div class="form-text">{{ form.device_id.help_text }}</div>
                        {% if form.device_id.errors %}
                            <div class="text-danger">{{ form.device_id.errors }}</div>
                        {% endif %}
                    </div>

                    <div class="mb-3">
                        <label for="{{ form.device_name.id_for_label }}" class="form-label">
                            Device Name <span class="text-danger">*</span>
                        </label>
                        {{ form.device_name }}
                        <div class="form-text">{{ form.device_name.help_text }}</div>
                        {% if form.device_name.errors %}
                            <div class="text-danger">{{ form.device_name.errors }}</div>
                        {% endif %}
                    </div>

                    <div class="mb-3">
                        <label for="{{ form.description.id_for_label }}" class="form-label">
                            Description
                        </label>
                        {{ form.description }}
                        <div class="form-text">{{ form.description.help_text }}</div>
                    </div>

                    <div class="mb-3">
                        <label for="{{ form.port.id_for_label }}" class="form-label">
                            Port <span class="text-danger">*</span>
                        </label>
                        {{ form.port }}
                        <div class="form-text">{{ form.port.help_text }}</div>
                        {% if form.port.errors %}
                            <div class="text-danger">{{ form.port.errors }}</div>
                        {% endif %}
                    </div>

                    <div class="d-grid gap-2 d-md-flex justify-content-md-start">
                        <button type="submit" class="btn btn-primary btn-lg">
                            ✓ Create Virtual Device
                        </button>
                        <a href="{% url 'discovery:virtual_device_list' %}" class="btn btn-secondary btn-lg">
                            Cancel
                        </a>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <div class="col-md-4">
        <div class="card bg-light">
            <div class="card-header">
                <h6>💡 Tips</h6>
            </div>
            <div class="card-body">
                <ul class="small">
                    <li><strong>Device ID:</strong> Must be unique on your network</li>
                    <li><strong>Port 47808:</strong> Standard BACnet port</li>
                    <li><strong>Port 47809+:</strong> Use for additional virtual devices</li>
                    <li><strong>Discoverability:</strong> Devices on standard port (47808) are more easily discovered</li>
                    <li><strong>Server:</strong> Make sure <code>run_virtual_devices</code> management command is running</li>
                </ul>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

**File 3:** Update `discovery/templates/discovery/dashboard.html`

**Add this button in the "Discovery Controls" card:**

```html
<!-- Add this after the existing buttons in dashboard.html -->
<a href="{% url 'discovery:virtual_device_list' %}" class="btn btn-success btn-lg">
    🖥️ Manage Virtual Devices
</a>
```

---

### **STEP 8: Testing End-to-End** (Day 6, ~2 hours)

**Complete workflow test:**

1. **Start management command:**
   ```bash
   python manage.py run_virtual_devices
   ```

2. **Start Django server (different terminal):**
   ```bash
   python manage.py runserver
   ```

3. **Test via Web UI:**
   - Go to http://127.0.0.1:8000
   - Click "Manage Virtual Devices"
   - Click "Create Virtual Device"
   - Fill form:
     - Device ID: 1001
     - Device Name: "Test Virtual Sensor"
     - Port: 47808
   - Submit form

4. **Verify in management command terminal:**
   - Should see: "Starting device 1001..."
   - Should see: "✓ Device 1001 started on port 47808"

5. **Test with BACnet browser (if available):**
   - Perform WhoIs scan
   - Look for Device ID 1001

6. **Test deletion:**
   - Click "Delete" button
   - Verify device stops and is removed

---

## 🎯 MVP Completion Checklist

### Core Functionality
- [ ] Django model for virtual devices
- [ ] Database migrations applied
- [ ] Management command runs virtual devices
- [ ] Service layer for device lifecycle
- [ ] Web forms with validation
- [ ] Views for create/list/delete
- [ ] URL routing configured
- [ ] Templates with Bootstrap styling
- [ ] End-to-end workflow tested

### Testing
- [ ] Can create virtual device via UI
- [ ] Device appears in database
- [ ] Management command starts device
- [ ] Device appears in list view
- [ ] Can delete device via UI
- [ ] Management command stops device
- [ ] Error handling works (duplicate ID, etc.)

### Documentation (Day 7-8)
- [ ] User guide: How to create virtual devices
- [ ] Admin guide: How to run the server
- [ ] Architecture documentation
- [ ] Known limitations documented
- [ ] Future enhancements listed

---

## 🚨 Common Issues & Solutions

### Issue 1: Port already in use
**Error:** `Address already in use`
**Solution:**
- Stop other BAC0 instances
- Use different port (47809)
- Check if `windows_integrated_server.py` is running

### Issue 2: Device not starting
**Check:**
- Is management command running?
- Is `is_running` set to True in database?
- Check management command logs
- Check port conflicts

### Issue 3: Device not discoverable
**Check:**
- Device on standard port 47808?
- Firewall blocking UDP traffic?
- BACnet browser on same subnet?
- Device actually running (check logs)?

### Issue 4: Changes not reflected
**Solution:**
- Management command checks every 5 seconds
- Wait a few seconds after creating device
- Check database: `is_running` field

---

## 📝 Daily Progress Tracking

### Day 2 (Today)
- [x] POC validated
- [ ] Django model created
- [ ] Migrations applied
- [ ] Model tested

### Day 3
- [ ] Management command created
- [ ] Management command tested
- [ ] Service layer created
- [ ] Service layer tested

### Day 4
- [ ] Forms created
- [ ] Views created
- [ ] URLs configured
- [ ] Basic flow tested

### Day 5-6
- [ ] Templates created
- [ ] UI styled
- [ ] End-to-end testing
- [ ] Bug fixes

### Day 7-8
- [ ] Documentation written
- [ ] Code cleanup
- [ ] Final testing
- [ ] Demo preparation

---

## 🎓 Learning Resources

**If stuck:**
- Django Models: https://docs.djangoproject.com/en/stable/topics/db/models/
- Django Forms: https://docs.djangoproject.com/en/stable/topics/forms/
- Management Commands: https://docs.djangoproject.com/en/stable/howto/custom-management-commands/
- BAC0: https://bac0.readthedocs.io/

**Your resources:**
- POC script: `poc_bac0_simple.py`
- Research doc: `TODO/bac0-virtual-device-research.md`
- Timeline: `TODO/internship-timeline-8-days.md`

---

Good luck with the implementation! 🚀
