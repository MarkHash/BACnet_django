# Windows Office Testing Plan
**Date:** 2025-09-29
**Location:** Office with Windows machine and real BACnet network
**Status:** 🎯 READY FOR TESTING

## Overview
Testing the hybrid architecture implementation that allows BACnet operations to run natively on Windows while keeping Docker services for web interface and database.

## What We've Already Implemented

### ✅ Hybrid Architecture Components
1. **Auto-detection System** - Platform automatically determines Windows vs Linux/Mac
2. **Database Task Communication** - Docker containers and Windows worker communicate via PostgreSQL
3. **Windows Native Worker** - `bacnet_native_worker.py` polls database for pending tasks
4. **Docker Configuration** - `docker-compose.windows.yml` for Windows-specific setup
5. **Task Model** - `BACnetTask` model for coordinating operations between environments

### ✅ Key Files Ready for Testing
- `bacnet_native_worker.py` - Windows worker that connects to real BACnet network
- `docker-compose.windows.yml` - Complete Docker configuration for Windows
- `discovery/models.py` - BACnetTask model for database communication
- `settings.py` - Auto-detection of Windows environment
- Updated views for Windows-safe task triggering

## Office Testing Procedure

### Step 1: Environment Setup
```bash
# Navigate to project directory
cd /path/to/BACnet_django

# Verify required files exist
ls docker-compose.windows.yml
ls bacnet_native_worker.py
```

### Step 2: Start Docker Services
```bash
# Start Docker services (web, database, Redis) - excludes BACnet worker
docker-compose -f docker-compose.windows.yml up -d

# Verify services are running
docker-compose ps
```

Expected output: Web, database, and Redis containers running. No BACnet worker container.

### Step 3: Install Python Dependencies (if needed)
```bash
# Install required packages for native worker
pip install django psycopg2 BAC0 python-dotenv

# Or if using virtual environment
pip install -r requirements.txt
```

### Step 4: Start Windows Native Worker
```bash
# Start the native BACnet worker
python bacnet_native_worker.py
```

Expected output:
```
🪟 Starting Native BACnet Worker for Windows...
📡 Using Windows host network for BACnet discovery
🗄️  Monitoring database for pending tasks...
```

### Step 5: Test BACnet Discovery
1. **Open web browser** → `http://localhost:8000`
2. **Navigate to discovery page**
3. **Click "Start Discovery"** button
4. **Monitor native worker console** for activity
5. **Check web interface** for discovered devices

### Step 6: Test Point Discovery
1. **Select a discovered device** from web interface
2. **Click "Discover Points"** for that device
3. **Monitor native worker** processing the task
4. **Verify points appear** in web interface

### Step 7: Test Reading Collection
1. **Click "Read All Values"** from web interface
2. **Monitor native worker** collecting readings
3. **Verify readings appear** in database and web interface

## Expected Results

### Windows Native Worker Should:
- ✅ Connect to office BACnet network (192.168.1.x range)
- ✅ Discover real BACnet devices (not mock data)
- ✅ Successfully read device points and values
- ✅ Store results in PostgreSQL database
- ✅ Display "Task completed" messages in console

### Web Interface Should:
- ✅ Show "Task created" messages when triggering operations
- ✅ Display real discovered devices with actual addresses
- ✅ Show actual BACnet points and current values
- ✅ Update in real-time as native worker processes tasks

### Database Should:
- ✅ Contain BACnetTask records with status progression (pending → running → completed)
- ✅ Store real device data from office BACnet network
- ✅ Show actual readings with timestamps

## Troubleshooting Guide

### If Native Worker Doesn't Start:
```bash
# Check Python path and Django setup
python -c "import django; print('Django OK')"
python -c "import BAC0; print('BAC0 OK')"

# Verify database connection
python manage.py check
```

### If No Devices Discovered:
- Verify office BACnet network is accessible
- Check Windows firewall settings for UDP port 47808
- Confirm `.env` file has correct `BACNET_IP` configuration
- Test with BAC0 directly: `python -c "import BAC0; bacnet = BAC0.lite(); print(bacnet.discover())"`

### If Database Connection Fails:
- Ensure Docker services are running: `docker-compose ps`
- Check database logs: `docker-compose logs db`
- Verify connection from Windows: `telnet localhost 5432`

### If Web Interface Shows Errors:
- Check Django logs in Docker: `docker-compose logs web`
- Verify task creation in database: Django admin at `http://localhost:8000/admin/`

## Success Criteria

### ✅ Phase 1: Basic Connectivity
- Docker services start successfully
- Native worker connects to database
- Web interface loads and responds

### ✅ Phase 2: BACnet Discovery
- Native worker discovers real office BACnet devices
- Device information appears in web interface
- Task status updates correctly in database

### ✅ Phase 3: Point Operations
- Point discovery works for real devices
- Reading collection retrieves actual values
- All data persists correctly in database

### ✅ Phase 4: End-to-End Validation
- Complete workflow from web trigger to data display
- Real-time updates between components
- No errors in logs or console output

## Network Configuration

### Office BACnet Network Expected:
- **Network Range:** 192.168.1.x
- **BACnet Port:** 47808 (UDP)
- **Expected Devices:** Industrial BACnet controllers, sensors, actuators
- **Device Types:** HVAC controllers, lighting panels, energy meters

### Environment Variables (`.env`):
```env
BACNET_IP=192.168.1.5:47808/24
# Adjust IP to match office network configuration
```

## Data Collection Goals

### Device Information:
- Device IDs and addresses
- Vendor information
- Device types and capabilities
- Network topology

### Point Data:
- Object types (Analog Input, Binary Output, etc.)
- Point names and descriptions
- Current values and units
- Data types and ranges

### Performance Metrics:
- Discovery time and success rate
- Reading collection speed
- Network response times
- Error rates and types

## Post-Testing Actions

### If Testing Successful:
1. **Document findings** - Device counts, network topology, performance
2. **Create test data backup** - Export discovered devices and readings
3. **Plan next development phase** - Data engineering and ML features
4. **Update documentation** - Add office network configuration details

### If Issues Found:
1. **Log detailed error messages** - Console output, Django logs, Docker logs
2. **Test network connectivity** - Ping tests, port scanning, firewall checks
3. **Validate configuration** - Environment variables, Docker setup, Python dependencies
4. **Create issue tracking** - Document problems for resolution

## Follow-up Development (After Successful Testing)

### Week 1: DRF Conversion
- Convert devices_status_api and device_trends_api to Django REST Framework
- Add auto-generated API documentation
- Professional portfolio enhancement

### Week 2-4: Data Engineering Features
- Real-time data pipeline with collected BACnet data
- Analytics dashboard using actual office device readings
- ML anomaly detection with real sensor patterns
- Energy optimization recommendations based on actual usage

## Files Modified During Implementation
- `discovery/models.py` - Added BACnetTask model
- `discovery/views.py` - Added Windows-safe task triggering
- `discovery/urls.py` - Updated to use new trigger functions
- `bacnet_project/settings.py` - Added Windows auto-detection
- `docker-compose.windows.yml` - Created Windows-specific Docker config
- `bacnet_native_worker.py` - Created standalone Windows worker
- `README.md` - Added Windows deployment instructions

## Technical Architecture Validated
```
┌─────────────────────────────────────────────────────────┐
│                Docker Services                          │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ Web (Django)    │  │ PostgreSQL DB   │              │
│  │ - Web Interface │◄─┤ - Task Queue    │◄─┐           │
│  │ - Task Creation │  │ - Device Data   │  │           │
│  │ - Data Display  │  │ - Readings      │  │           │
│  └─────────────────┘  └─────────────────┘  │           │
└─────────────────────────────────────────────┼───────────┘
                                              │
┌─────────────────────────────────────────────┼───────────┐
│                Windows Host                 │           │
│  ┌─────────────────────────────────────────┐│           │
│  │        Native BACnet Worker             ││           │
│  │  ┌─────────────────────────────────────┐││           │
│  │  │ bacnet_native_worker.py            │├┘           │
│  │  │ - Polls database for tasks         ││             │
│  │  │ - Connects to office BACnet network││             │
│  │  │ - Uses Windows native networking   ││             │
│  │  │ - Stores results in database       ││             │
│  │  └─────────────────────────────────────┘│             │
│  └─────────────────────────────────────────┘             │
└───────────────────────────────────────────────────────────┘
                            │
                            ▼
                ┌─────────────────────┐
                │  Office BACnet      │
                │  Network            │
                │  (192.168.1.x)      │
                │  - Real devices     │
                │  - Live data        │
                └─────────────────────┘
```

---
**Implementation Time:** Already completed (~6 days total development)
**Testing Time:** 1-2 hours expected
**Office Network:** Real BACnet devices for validation
**Next Phase:** Data engineering and ML features with real data