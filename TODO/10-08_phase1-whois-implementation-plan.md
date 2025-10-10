# Phase 1: WhoIs Implementation Plan
**Date:** October 8, 2025
**Branch:** feat/enhanced-virtual-devices
**Goal:** Make virtual devices discoverable via broadcast WhoIs requests

## Problem Analysis

### Current Issue
- Virtual devices created with `BAC0.lite(deviceId=X, port=Y)` are not discoverable
- `bacnet.discover()` returns `None` - devices don't respond to WhoIs broadcasts
- Devices only have basic device object, no additional BACnet objects

### Root Cause Discovery
- **BAC0 Documentation Insight**: Devices need **local BACnet objects** to be fully discoverable
- **Real BACnet Behavior**: Industrial devices always have multiple objects (sensors, controls, outputs)
- **Discovery Tool Expectations**: Tools look for devices with meaningful functionality, not empty devices

## Solution: Local BACnet Objects

### Key Documentation Finding
From https://bac0.readthedocs.io/en/latest/local_objects.html:

```python
# Current: Bare device (minimal, hard to discover)
bacnet = BAC0.lite(deviceId=1002, port=47809)
# Only has: Device Object

# Enhanced: Device with local objects (fully discoverable)
async with BAC0.lite(deviceId=1002, localObjName="Temperature Sensor") as dev:
    # Add analog input (temperature sensor)
    analog_input(name="Temperature",
                 description="Room temperature",
                 properties={"units": "degreesCelsius"})

    # Register objects to make them discoverable
    analog_input.add_objects_to_application(dev)
```

## Implementation Plan

### Phase 1a: Enhanced Device Creation
**File:** `discovery/management/commands/run_virtual_devices.py`

**Changes Required:**
1. **Import local object factories**
   ```python
   from BAC0.core.devices.local.models import (
       analog_input, analog_output, binary_input, binary_output
   )
   ```

2. **Convert to async pattern**
   ```python
   async def start_device_async(self, device):
       async with BAC0.lite(
           deviceId=device.device_id,
           port=device.port,
           localObjName=device.device_name
       ) as bacnet_device:
           # Add local objects here
           await self.create_device_objects(bacnet_device, device)
           # Keep device running
           while device.device_id in self.running_devices:
               await asyncio.sleep(1)
   ```

3. **Add realistic BACnet objects**
   ```python
   def create_device_objects(self, bacnet_device, device):
       """Create appropriate BACnet objects based on device type"""
       # Default objects for all devices
       analog_input(name="Status",
                    description="Device status",
                    properties={"units": "noUnits"})

       # Device-specific objects based on name
       if "temperature" in device.device_name.lower():
           analog_input(name="Temperature",
                        description="Temperature reading",
                        properties={"units": "degreesCelsius"})
           analog_input(name="Humidity",
                        description="Humidity reading",
                        properties={"units": "percent"})

       elif "hvac" in device.device_name.lower():
           analog_output(name="Setpoint",
                         description="Temperature setpoint",
                         properties={"units": "degreesCelsius"})
           binary_output(name="Fan",
                         description="Fan control",
                         properties={"activeText": "on", "inactiveText": "off"})

       elif "lighting" in device.device_name.lower():
           binary_output(name="Lights",
                         description="Light switch",
                         properties={"activeText": "on", "inactiveText": "off"})
           analog_output(name="Dimmer",
                         description="Dimmer level",
                         properties={"units": "percent"})

       # Register all objects
       analog_input.add_objects_to_application(bacnet_device)
       analog_output.add_objects_to_application(bacnet_device)
       binary_input.add_objects_to_application(bacnet_device)
       binary_output.add_objects_to_application(bacnet_device)
   ```

### Phase 1b: Object Type Mapping
**Device Name Patterns → BACnet Objects:**

| Device Type | Objects Created |
|-------------|-----------------|
| **Temperature Sensor** | Analog Input: Temperature (°C), Humidity (%) |
| **HVAC Controller** | Analog Output: Setpoint (°C), Binary Output: Fan (on/off) |
| **Lighting Panel** | Binary Output: Lights (on/off), Analog Output: Dimmer (%) |
| **Energy Meter** | Analog Input: Power (kW), Energy (kWh), Voltage (V) |
| **Generic Device** | Analog Input: Status, Binary Input: Alarm |

### Phase 1c: Service Management Updates
**Handle async pattern in management command:**

```python
def handle(self, *args, **options):
    # Set up event loop for async devices
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(self.run_service())
    finally:
        loop.close()

async def run_service(self):
    """Main service loop with async device management"""
    await self.start_all_devices_async()

    while not self.shutdown:
        await asyncio.sleep(5)
        await self.check_device_states_async()
```

## Testing Plan

### Test 1: Enhanced Device Startup
**Expected Output:**
```
Starting Virtual BACnet Device server...
Starting device 1002...
✓ Device 1002 (Temperature Sensor) started with 3 objects on port 47809
  - Device Object: 1002
  - Analog Input: Temperature (°C)
  - Analog Input: Humidity (%)
  - Analog Input: Status
```

### Test 2: Discovery Validation
**From separate container:**
```python
# Test discovery
devices = bacnet.discover()
print('Found devices:', devices)
# Expected: [('172.18.0.7', 47809, 1002)]

# Test object list
objects = await bacnet.read('172.18.0.7:47809 device 1002 objectList')
print('Device objects:', objects)
# Expected: [device:1002, analogInput:1, analogInput:2, analogInput:3]

# Test object reading
temp = await bacnet.read('172.18.0.7:47809 analogInput:1 presentValue')
print('Temperature:', temp)
# Expected: Numeric value (e.g., 72.5)
```

### Test 3: Object Property Access
**Verify full BACnet functionality:**
```python
# Read object name
name = await bacnet.read('172.18.0.7:47809 analogInput:1 objectName')
# Expected: "Temperature"

# Read engineering units
units = await bacnet.read('172.18.0.7:47809 analogInput:1 units')
# Expected: "degreesCelsius"

# Read description
desc = await bacnet.read('172.18.0.7:47809 analogInput:1 description')
# Expected: "Temperature reading"
```

## Success Criteria

### ✅ Primary Goals
1. **Discovery Success**: `bacnet.discover()` returns virtual device information
2. **Object List Access**: Device object list shows all created objects
3. **Property Reading**: Can read individual object properties
4. **Realistic Behavior**: Device behaves like real BACnet equipment

### ✅ Secondary Goals
1. **Multiple Device Support**: All virtual devices become discoverable
2. **Device Type Recognition**: Different device types have appropriate objects
3. **Service Stability**: Async pattern doesn't break existing functionality
4. **Error Handling**: Graceful failure recovery

## Implementation Timeline

### Day 1: Core Implementation (2-3 hours)
- **Hour 1**: Import object factories and convert to async pattern
- **Hour 2**: Implement object creation logic and device mapping
- **Hour 3**: Test basic device startup and object registration

### Day 1: Testing & Validation (1-2 hours)
- **30 min**: Test enhanced device discovery
- **30 min**: Validate object list and property reading
- **30 min**: Test multiple devices with different object types
- **30 min**: Document results and create test cases

## Risk Assessment

### Low Risk Items ✅
- **BAC0 Feature**: Using documented local object functionality
- **Backward Compatibility**: Can revert to current implementation
- **Incremental**: Changes are isolated to device creation logic

### Medium Risk Items ⚠️
- **Async Conversion**: Management command pattern change
- **Object Factory Usage**: New BAC0 API surface area
- **Memory Usage**: Multiple objects per device

### Mitigation Strategies
1. **Backup Current Code**: Git branch allows easy rollback
2. **Incremental Testing**: Test each component separately
3. **Error Handling**: Comprehensive try/catch blocks
4. **Documentation**: Record all changes and test results

## Expected Outcomes

### Technical Benefits
- **Full BACnet Compliance**: Devices behave like real equipment
- **Enhanced Testing**: Can test complex BACnet scenarios
- **Protocol Validation**: Verify BMS integration properly

### Portfolio Benefits
- **Industry Knowledge**: Demonstrates real BACnet understanding
- **Problem Solving**: Shows systematic debugging approach
- **Technical Depth**: Moving beyond basic connectivity to full protocol

### Future Enablement
- **Phase 2 Ready**: Objects support value updates and control
- **Phase 3 Ready**: Foundation for COV notifications and alarms
- **Production Ready**: Creates realistic testing environment

## Next Phase Preview

### Phase 2: Controllable Objects (After Discovery Success)
- Add writable properties to output objects
- Implement value update mechanisms via web interface
- Add real-time synchronization between web UI and BACnet objects

### Phase 3: Advanced Features
- Change of Value (COV) notifications
- BACnet priority arrays for outputs
- Alarm and event objects
- Trending and historical data

---

**Implementation Status:** Ready to begin
**Dependencies:** BAC0 library, async/await support
**Testing Environment:** Docker containers with separate BACnet clients
**Success Metric:** Virtual devices appear in `bacnet.discover()` results with full object lists