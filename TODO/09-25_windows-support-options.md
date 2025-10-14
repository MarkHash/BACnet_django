# Windows Support Implementation Options

## 🎯 Current Status
- ✅ BAC0 works perfectly on Windows host (finds 3 BACnet devices)
- ✅ Docker infrastructure (Postgres, Redis) working
- ❌ Container subprocess cannot access Windows host IP `192.168.1.5`

## 🔧 Architecture Options

### Option A: Full Host Execution
**Run Django + Celery natively on Windows, Docker for infrastructure only**

**Pros:**
- ✅ Clean network access to BACnet devices
- ✅ No subprocess complexity
- ✅ Native Windows performance
- ✅ Easy debugging

**Cons:**
- ❌ Need to manage multiple processes

**Setup:**
1. Use existing `venv312` (already has all packages)
2. Update `.env` to use `DATABASE_URL_HOST` and `REDIS_URL_HOST`
3. Run services with process manager (see below)

### Option B: Docker Host Networking
**Use Docker Compose with `network_mode: host`**

**Pros:**
- ✅ Single `docker-compose up` command
- ✅ Access to Windows host network
- ✅ Container benefits retained

**Cons:**
- ❌ Windows Docker Desktop host networking limitations
- ❌ Potential security concerns

**Setup:**
```yaml
services:
  web:
    network_mode: host
    environment:
      - DATABASE_URL=${DATABASE_URL_HOST}
```

### Option C: Separate BACnet Service
**Run dedicated BACnet service on Windows, communicate via API**

**Pros:**
- ✅ Clean separation of concerns
- ✅ Both contexts work optimally

**Cons:**
- ❌ More complex architecture
- ❌ Additional API development needed

## 🔧 Process Management Options (for Option A)

### Option 1: Celery Multi (Built-in)
```bash
celery multi start worker1 worker2 beat \
  -A bacnet_project \
  --pidfile=/tmp/%n.pid \
  --logfile=/tmp/%n%I.log \
  -Q:worker1 celery \
  -Q:worker2 bacnet \
  --beat:beat
```

### Option 2: Honcho/Foreman ⭐ RECOMMENDED
```bash
pip install honcho

# Create Procfile
web: python manage.py runserver
worker: celery -A bacnet_project worker --exclude-queues=bacnet
bacnet: celery -A bacnet_project worker --queues=bacnet
beat: celery -A bacnet_project beat

# Start everything
honcho start
```

### Option 3: Python Script
```python
# run_services.py
import subprocess
import threading

def run_service(cmd):
    subprocess.run(cmd, shell=True)

services = [
    "python manage.py runserver",
    "celery -A bacnet_project worker --exclude-queues=bacnet",
    "celery -A bacnet_project worker --queues=bacnet",
    "celery -A bacnet_project beat"
]

for cmd in services:
    threading.Thread(target=run_service, args=(cmd,)).start()
```

### Option 4: Windows Batch Script
```batch
@echo off
start "Django" python manage.py runserver
start "Celery Worker" celery -A bacnet_project worker --exclude-queues=bacnet
start "BACnet Worker" celery -A bacnet_project worker --queues=bacnet
start "Celery Beat" celery -A bacnet_project beat
```

## 📋 Next Steps

1. **Choose Architecture**: Option A (Full Host) or Option B (Host Networking)
2. **Choose Process Manager**: Honcho recommended for development
3. **Update Configuration**: Environment variables for chosen option
4. **Test Implementation**: Verify BACnet discovery works end-to-end
5. **Document Setup**: Create setup instructions for other developers

## 🎯 Recommendation

**Start with Option A + Honcho** because:
- Lowest complexity
- Best Windows BACnet performance
- Easy to debug and develop
- Can always containerize later if needed