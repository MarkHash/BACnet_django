# Virtual Device Testing Guide
**Date:** October 8, 2025
**Purpose:** Complete step-by-step testing procedures for virtual BACnet devices

## Prerequisites

### Environment Setup
- Docker and docker-compose installed
- Project running with `docker-compose up`
- Multiple terminal windows available
- Basic understanding of BACnet protocol

### Required Services
1. **Web Application**: Django app running on http://127.0.0.1:8000
2. **Database**: PostgreSQL container
3. **Virtual Device Service**: Management command for device creation

## Test Suite 1: Web Interface Testing

### Test 1.1: Access Virtual Device Management
**Objective:** Verify web interface is accessible

**Steps:**
1. Open browser to http://127.0.0.1:8000
2. Click "🖥️ Manage Virtual Devices" button
3. Verify navigation to virtual device list page

**Expected Results:**
- ✅ Virtual device list page loads
- ✅ Shows statistics (Total Virtual Devices, Running Devices)
- ✅ Shows "Create Virtual Device" button
- ✅ Shows empty table if no devices exist

**Troubleshooting:**
- If button missing: Check dashboard template integration
- If 404 error: Verify URL patterns in `discovery/urls.py`

### Test 1.2: Create Virtual Device via Web Interface
**Objective:** Test device creation through UI

**Steps:**
1. Click "➕ Create Virtual Device" button
2. Fill in form:
   - **Device ID**: `1001`
   - **Device Name**: `Test Temperature Sensor`
   - **Description**: `Virtual temperature sensor for testing`
   - **Port**: `47809` (or leave default 47808)
3. Click "✓ Create Virtual Device"

**Expected Results:**
- ✅ Form validates successfully
- ✅ Redirects to virtual device list
- ✅ New device appears in table
- ✅ Status shows as "Running"
- ✅ Success message displayed

**Troubleshooting:**
- If validation fails: Check device ID uniqueness and port range
- If form doesn't submit: Check CSRF token and form validation
- If device not appearing: Check database connection

### Test 1.3: Device Validation Testing
**Objective:** Verify form validation works correctly

**Test Cases:**

**A. Duplicate Device ID**
1. Try to create device with existing ID (e.g., 1001)
2. **Expected:** Error message "Device ID 1001 already exists"

**B. Invalid Device ID Range**
1. Try device ID: `-1`
2. **Expected:** "Device ID must be between 0 and 4194303"
3. Try device ID: `5000000`
4. **Expected:** Same error message

**C. Invalid Port Range**
1. Try port: `500`
2. **Expected:** "Port must be between 1024 and 65535"
3. Try port: `70000`
4. **Expected:** Same error message

**D. Empty Required Fields**
1. Leave Device ID empty
2. **Expected:** "This field is required"
3. Leave Device Name empty
4. **Expected:** "This field is required"

## Test Suite 2: Database and Service Testing

### Test 2.1: Database Verification
**Objective:** Confirm device stored correctly in database

**Steps:**
```bash
# Terminal 1: Access Django shell
docker-compose exec web python manage.py shell -c "
from discovery.models import VirtualBACnetDevice
devices = VirtualBACnetDevice.objects.all()
for d in devices:
    print(f'Device {d.device_id}: {d.device_name} on port {d.port}, running: {d.is_running}')
"
```

**Expected Results:**
- ✅ Device 1001 appears in database
- ✅ All properties correctly stored
- ✅ `is_running` field is `True`
- ✅ Timestamps populated

### Test 2.2: Virtual Device Service Startup
**Objective:** Test management command starts devices

**Steps:**
```bash
# Terminal 2: Start virtual device service
docker-compose exec web python manage.py run_virtual_devices
```

**Expected Results:**
```
Starting Virtual BACnet Device server...
Starting device 1001...
2025-10-08 XX:XX:XX,XXX - INFO | Starting BAC0 version XX.XX.XX (Lite)
2025-10-08 XX:XX:XX,XXX - INFO | Using ip : 172.18.0.X:47809 on port 47809
2025-10-08 XX:XX:XX,XXX - INFO | Device instance (id) : 1001
✓ Device 1001 started on port 47809
```

**Key Indicators:**
- ✅ "Starting device 1001" message
- ✅ BAC0 initialization logs
- ✅ IP address and port assignment
- ✅ Device instance ID matches
- ✅ Success checkmark with port confirmation
- ✅ COV task logs every 5 seconds

**Troubleshooting:**
- If "Failed to start": Check port conflicts or device ID conflicts
- If no output: Verify database has devices with `is_running=True`
- If permission errors: Check Docker container network permissions

### Test 2.3: Service Process Verification
**Objective:** Confirm service is running and listening

**Steps:**
```bash
# Terminal 3: Check running processes
docker-compose exec web ps aux | grep python

# Check port listening
docker-compose exec web netstat -ulnp | grep 47809
```

**Expected Results:**
- ✅ `run_virtual_devices` process visible
- ✅ Port 47809 shows as listening
- ✅ Process owned by correct user

## Test Suite 3: Network Connectivity Testing

### Test 3.1: Docker Network Discovery
**Objective:** Verify devices accessible on Docker network

**Steps:**
```bash
# Terminal 4: Create test container on same network
docker run --rm -it --network bacnet_django_default python:3.9-slim bash

# Inside container: Install BAC0
apt-get update && apt-get install -y gcc python3-dev
pip install BAC0
```

**Expected Results:**
- ✅ Container starts on same network
- ✅ BAC0 installs successfully
- ✅ Network connectivity to virtual device containers

### Test 3.2: Basic Network Connectivity
**Objective:** Test IP-level connectivity

**Steps:**
```bash
# Inside test container: Get virtual device IP
# Note the IP from virtual device service logs (e.g., 172.18.0.7)

# Test basic connectivity (if ping available)
apt-get install -y iputils-ping
ping -c 3 172.18.0.7
```

**Expected Results:**
- ✅ Ping responses from virtual device container
- ✅ 0% packet loss
- ✅ Reasonable response times

## Test Suite 4: BACnet Protocol Testing

### Test 4.1: Direct Property Reading
**Objective:** Test BACnet communication to virtual device

**Steps:**
```bash
# Inside test container: Test direct communication
python -c "
import BAC0
import asyncio

async def test_device():
    print('🎯 Testing device 1001 communication...')
    try:
        bacnet = BAC0.lite(port=47810)  # Different port to avoid conflict
        await asyncio.sleep(2)

        # Read basic device properties
        object_list = await bacnet.read('172.18.0.X:47809 device 1001 objectList')
        print(f'✅ Object List: {object_list}')

        device_name = await bacnet.read('172.18.0.X:47809 device 1001 objectName')
        print(f'✅ Device Name: {device_name}')

        vendor_id = await bacnet.read('172.18.0.X:47809 device 1001 vendorIdentifier')
        print(f'✅ Vendor ID: {vendor_id}')

        bacnet.disconnect()
        print('✅ Direct communication test passed!')

    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

asyncio.run(test_device())
"
```

**Expected Results:**
- ✅ Object List: `[(<ObjectType: device>, 1001)]`
- ✅ Device Name: `BAC0` (or custom name)
- ✅ Vendor ID: numeric value
- ✅ No connection errors
- ✅ Clean disconnect

**Troubleshooting:**
- Replace `172.18.0.X` with actual IP from service logs
- If timeout: Check firewall or network configuration
- If "device not found": Verify device ID and IP address

### Test 4.2: Broadcast Discovery Testing
**Objective:** Test if device responds to discovery

**Steps:**
```bash
# Inside test container: Test broadcast discovery
python -c "
import BAC0
import asyncio

async def test_discovery():
    print('🔍 Testing broadcast discovery...')
    try:
        bacnet = BAC0.lite(port=47809)  # Same port as virtual device
        await asyncio.sleep(3)

        devices = bacnet.discover()
        print(f'📡 Discovery result: {devices}')

        if devices:
            print('✅ Virtual device discovered via broadcast!')
            for device in devices:
                print(f'  Device: {device}')
        else:
            print('⚠️  No devices found via broadcast (expected with current implementation)')
            print('   This indicates need for Phase 1 enhancement (WhoIs response)')

        bacnet.disconnect()

    except Exception as e:
        print(f'❌ Discovery error: {e}')

asyncio.run(test_discovery())
"
```

**Expected Results (Current Implementation):**
- ✅ Discovery runs without errors
- ⚠️ Result: `None` (expected - basic virtual device doesn't respond to broadcasts)
- ✅ Clean execution and disconnect

**Expected Results (After Phase 1 Enhancement):**
- ✅ Discovery finds virtual device
- ✅ Device information returned in discovery result

## Test Suite 5: Multiple Device Testing

### Test 5.1: Create Multiple Virtual Devices
**Objective:** Test system with multiple devices

**Steps:**
1. Create second device via web interface:
   - Device ID: `1002`
   - Name: `Test Humidity Sensor`
   - Port: `47810`

2. Create third device:
   - Device ID: `1003`
   - Name: `Test Pressure Sensor`
   - Port: `47811`

**Expected Results:**
- ✅ All devices appear in virtual device list
- ✅ Each device has unique ID and port
- ✅ Statistics update correctly

### Test 5.2: Multiple Device Service Test
**Objective:** Verify service handles multiple devices

**Steps:**
```bash
# Restart virtual device service (Ctrl+C, then restart)
docker-compose exec web python manage.py run_virtual_devices
```

**Expected Results:**
```
Starting Virtual BACnet Device server...
Starting device 1001...
✓ Device 1001 started on port 47809
Starting device 1002...
✓ Device 1002 started on port 47810
Starting device 1003...
✓ Device 1003 started on port 47811
```

- ✅ All devices start successfully
- ✅ Each device gets unique port
- ✅ No port conflicts
- ✅ All devices show COV task activity

### Test 5.3: Multi-Device Communication
**Objective:** Test communication to all devices

**Steps:**
```bash
# Test each device from test container
python -c "
import BAC0
import asyncio

async def test_all_devices():
    devices_to_test = [
        ('172.18.0.X', 47809, 1001),
        ('172.18.0.X', 47810, 1002),
        ('172.18.0.X', 47811, 1003)
    ]

    bacnet = BAC0.lite(port=47812)  # Different port
    await asyncio.sleep(2)

    for ip, port, device_id in devices_to_test:
        try:
            device_name = await bacnet.read(f'{ip}:{port} device {device_id} objectName')
            print(f'✅ Device {device_id} on port {port}: {device_name}')
        except Exception as e:
            print(f'❌ Device {device_id} failed: {e}')

    bacnet.disconnect()

asyncio.run(test_all_devices())
"
```

**Expected Results:**
- ✅ All devices respond successfully
- ✅ Each device returns correct name
- ✅ No port conflicts or communication errors

## Test Suite 6: Error Handling and Edge Cases

### Test 6.1: Device Deletion Testing
**Objective:** Test device lifecycle management

**Steps:**
1. Delete device 1003 via web interface
2. Check service logs for stop behavior
3. Verify device removed from database

**Expected Results:**
- ✅ Device removed from web interface
- ✅ Service stops device gracefully
- ✅ Database record deleted
- ✅ Port released for reuse

### Test 6.2: Service Restart Testing
**Objective:** Test service recovery and state management

**Steps:**
1. Stop virtual device service (Ctrl+C)
2. Create new device via web interface
3. Restart service
4. Verify all devices start correctly

**Expected Results:**
- ✅ Service stops all devices cleanly
- ✅ New device appears in database
- ✅ Service restart picks up all devices
- ✅ Both existing and new devices start

### Test 6.3: Port Conflict Testing
**Objective:** Test port conflict handling

**Steps:**
1. Try to create device with port already in use
2. Verify appropriate error handling

**Expected Results:**
- ✅ Service detects port conflict
- ✅ Error logged appropriately
- ✅ Device marked as not running
- ✅ Web interface shows error status

## Test Results Documentation Template

### Test Execution Record
```
Test Date: ___________
Tester: ___________
Environment: Docker/Local/Production

Test Suite 1 - Web Interface:
[ ] Test 1.1: Access Virtual Device Management
[ ] Test 1.2: Create Virtual Device via Web Interface
[ ] Test 1.3: Device Validation Testing

Test Suite 2 - Database and Service:
[ ] Test 2.1: Database Verification
[ ] Test 2.2: Virtual Device Service Startup
[ ] Test 2.3: Service Process Verification

Test Suite 3 - Network Connectivity:
[ ] Test 3.1: Docker Network Discovery
[ ] Test 3.2: Basic Network Connectivity

Test Suite 4 - BACnet Protocol:
[ ] Test 4.1: Direct Property Reading
[ ] Test 4.2: Broadcast Discovery Testing

Test Suite 5 - Multiple Devices:
[ ] Test 5.1: Create Multiple Virtual Devices
[ ] Test 5.2: Multiple Device Service Test
[ ] Test 5.3: Multi-Device Communication

Test Suite 6 - Error Handling:
[ ] Test 6.1: Device Deletion Testing
[ ] Test 6.2: Service Restart Testing
[ ] Test 6.3: Port Conflict Testing

Issues Found:
- Issue 1: ________________
- Issue 2: ________________

Overall Result: PASS/FAIL
Notes: ________________
```

## Common Troubleshooting

### Issue: Virtual Device Service Won't Start
**Symptoms:** No startup logs, no devices created
**Solutions:**
1. Check database connectivity
2. Verify Django settings
3. Check for existing processes on ports
4. Review device model validation

### Issue: BACnet Communication Fails
**Symptoms:** Timeouts, "device not found" errors
**Solutions:**
1. Verify IP addresses from service logs
2. Check Docker network configuration
3. Confirm port numbers match
4. Test basic network connectivity

### Issue: Web Interface Errors
**Symptoms:** 404, 500 errors, form validation issues
**Solutions:**
1. Check URL patterns
2. Verify template inheritance
3. Review form validation logic
4. Check CSRF token configuration

### Issue: Multiple Device Conflicts
**Symptoms:** Devices fail to start, port conflicts
**Solutions:**
1. Ensure unique device IDs
2. Assign different ports to each device
3. Check for existing processes
4. Review service startup sequence

## Success Criteria Summary

**Complete Success:**
- ✅ All 6 test suites pass
- ✅ Virtual devices create, start, and communicate
- ✅ Web interface fully functional
- ✅ Multiple devices work simultaneously
- ✅ Proper error handling and recovery

**Partial Success (Current State):**
- ✅ Direct BACnet communication works
- ✅ Web interface and database functional
- ⚠️ Broadcast discovery needs enhancement (Phase 1)
- ✅ Service management working

This testing guide provides comprehensive validation of the virtual device system and identifies areas for future enhancement!