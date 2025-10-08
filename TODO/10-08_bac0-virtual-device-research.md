# BAC0 Virtual Device Research Summary

**Date:** October 7, 2025
**Purpose:** Research findings on creating virtual BACnet devices using BAC0 library
**Context:** Company requirement to create discoverable virtual BACnet devices on the network

---

## 🎯 Key Discovery

**Every BAC0 instance IS a BACnet device!**

When you create a BAC0 connection with `BAC0.lite()`, you're not just creating a client - you're creating a **full BACnet device** that:
- Has its own Device ID
- Responds to WhoIs requests (discoverable)
- Can be found by other BACnet tools
- Acts as both CLIENT and SERVER

---

## 📚 Research Sources

### Primary Documentation
1. **BAC0 Official Documentation - Controller Guide**
   - URL: https://bac0.readthedocs.io/en/latest/controller.html
   - Key info: How to define devices and interact with points
   - Covers: Device creation, point reading/writing, property management

2. **BAC0 Official Documentation - Connection Guide**
   - URL: https://bac0.readthedocs.io/en/latest/connect.html
   - Key info: How to start BAC0 and create BACnet instances

3. **BAC0 Main Documentation**
   - URL: https://bac0.readthedocs.io/
   - Overview of BAC0 library capabilities

### Community Discussions
4. **GitHub Issue #146 - Creating Virtual BACnet Devices**
   - URL: https://github.com/ChristianTremblay/BAC0/issues/146
   - Key discussion on virtual device creation
   - Shows example of creating multiple devices on different ports
   - Code examples of device-to-device communication

5. **Stack Overflow - Virtual BACnet Devices**
   - URL: https://stackoverflow.com/questions/57156388/how-to-create-virtual-bacnet-devices-and-implementing-python-library
   - Related to same GitHub issue #146

### Repository
6. **BAC0 GitHub Repository**
   - URL: https://github.com/ChristianTremblay/BAC0
   - Main source code repository
   - Test suite shows virtual device examples

7. **BAC0 PyPI Package**
   - URL: https://pypi.org/project/BAC0/
   - Package information and installation

---

## 💡 Key Findings

### 1. Virtual Device Creation
```python
# Creates a BACnet device with custom ID
bacnet = BAC0.lite(deviceId=999)

# This device is now:
# - Discoverable on the network
# - Responds to WhoIs requests
# - Has Device ID 999
# - Running on port 47808 (default)
```

### 2. Multiple Virtual Devices
```python
# Device 1 on standard port
device1 = BAC0.lite(deviceId=1001, port=47808)

# Device 2 on different port (to avoid conflict)
device2 = BAC0.lite(deviceId=1002, port=47809)
```

**Important:** Each BAC0 instance needs its own port. Standard BACnet port is 47808.

### 3. Point Management

**Reading Points:**
- Use bracket syntax: `device['point_name']`
- Read properties: `await device.read_property(prop)`

**Writing Points:**
- Direct assignment: `device['point_name'] = 23`
- Outputs override at priority 8
- Inputs require out-of-service mode for simulation

**Releasing Points:**
- Return to auto: `device['point_name'] = 'auto'`

### 4. Device Definition with Custom Objects
```python
# Define custom object list
my_obj_list = [
    ('file', 1),
    ('analogInput', 2),
    ('analogInput', 3)
]

# Create device with custom objects
device = await BAC0.device('2:5', 5, bacnet, object_list=my_obj_list)
```

---

## ✅ What Works (Confirmed)

1. **Basic Virtual Device Creation**
   - ✅ BAC0.lite() creates discoverable device
   - ✅ Can specify custom Device ID
   - ✅ Device responds to WhoIs
   - ✅ Standard BACnet port 47808

2. **Multiple Devices**
   - ✅ Can create multiple devices on different ports
   - ✅ Devices can discover each other
   - ⚠️ Non-standard ports may not be auto-discovered by all tools

3. **Current Project Status**
   - ✅ Already using BAC0 in `discovery/services.py`
   - ✅ No BACpypes conflict (we're not using BACpypes)
   - ✅ Port 47808 available for virtual devices (if we stop client during creation)

---

## ⚠️ Challenges Identified

### 1. **Adding Custom Virtual Points**
- Creating the device is easy
- Adding custom points (analogInput, binaryOutput, etc.) is more complex
- Requires deeper understanding of BAC0/BACpypes3 API
- Limited documentation on this specific use case

### 2. **Port Management**
- Each virtual device needs its own port
- Standard port: 47808
- Additional devices: 47809, 47810, etc.
- Non-standard ports harder for other tools to discover

### 3. **Process Lifecycle**
- BAC0 instance must keep running continuously
- Django web requests are stateless (start/stop)
- Need background process:
  - Django management command
  - Celery long-running task
  - Separate Python service

### 4. **Database Synchronization**
- User creates virtual device in Django UI
- Need to start corresponding BAC0 instance
- If Django/process restarts, virtual devices disappear
- Must recreate from database on startup

### 5. **Client vs Server Conflict**
- Current setup: BAC0.lite() for discovery (client mode)
- New requirement: BAC0 instance for virtual device (server mode)
- Both need port 47808
- Solutions:
  - Use single BAC0 instance for both (recommended)
  - Use different ports (complicates discovery)
  - Stop client when serving, vice versa

---

## 🏗️ Architecture Considerations

### Current Setup
```
discovery/services.py
    ↓
BACnetService class
    ↓
BAC0.lite() - Creates temporary connection for discovery
    ↓
Discovers real devices → Saves to database
```

### Required for Virtual Devices
```
Django Web Interface
    ↓
VirtualDeviceService (NEW)
    ↓
BAC0.lite(deviceId=X) - Long-running instance
    ↓
Virtual device stays on network (discoverable)
```

### Integration Challenge
```
Problem: Both need port 47808

Solution Options:
1. Single BAC0 instance (client + server combined)
2. Different ports (47808 for client, 47809+ for virtual devices)
3. Start/stop instances as needed (complex state management)
```

---

## 📝 Implementation Recommendations

### **Phase 1: Proof of Concept (Recommended Starting Point)**
1. Create standalone Python script
2. Use BAC0.lite(deviceId=999)
3. Test discoverability with Yabe or BACnet browser
4. Verify other tools can see the virtual device
5. Don't worry about custom points yet

**Goal:** Confirm BAC0 virtual devices work on your network

### **Phase 2: Simple Django Integration**
1. Create management command: `python manage.py run_virtual_device_server`
2. Hard-code one virtual device (Device ID 999)
3. Keep it simple - no custom points
4. Focus on keeping process alive
5. Test starting/stopping

**Goal:** Prove concept works with Django

### **Phase 3: Database-Driven Virtual Devices**
1. Create Django models: `VirtualBACnetDevice`
2. Web form to create virtual devices
3. Service layer to manage BAC0 instances
4. Port allocation strategy
5. Database sync on startup

**Goal:** User can create virtual devices via UI

### **Phase 4: Custom Points (Advanced)**
1. Research BACpypes3 API for object creation
2. Add point models and forms
3. Create analogInput, analogOutput objects
4. Allow value updates via UI

**Goal:** Full-featured virtual devices with points

---

## 🎓 Additional Learning Resources

1. **BAC0 Test Suite**
   - URL: https://github.com/ChristianTremblay/BAC0/blob/master/tests/conftest.py
   - Contains examples of virtual devices communicating

2. **BACpypes Documentation** (BAC0's foundation)
   - URL: https://bacpypes.readthedocs.io/
   - Lower-level API documentation

3. **BACpypes3** (Modern version BAC0 uses)
   - BAC0 23.7.3 uses BACpypes3
   - More async-focused

---

## 🤔 Questions for Decision Making

Before implementation, clarify:

1. **How many virtual devices?**
   - One device = Simple (one port)
   - Multiple devices = Complex (port management)

2. **Do virtual devices need custom points?**
   - No points = Easy (just device shell)
   - Custom points = Complex (requires more research)

3. **What should points represent?**
   - Simulated sensors?
   - Gateway to other systems?
   - Test data?

4. **How will devices stay running?**
   - Management command (development)?
   - Celery task (production)?
   - Separate service (most robust)?

5. **Discovery vs Serving priority?**
   - Discover real devices (current feature)
   - Serve virtual devices (new feature)
   - Both simultaneously (requires careful design)

---

## 📊 Comparison: Current vs Required

| Feature | Current (Discovery Client) | Required (Virtual Device Server) |
|---------|---------------------------|----------------------------------|
| Library | BAC0 ✅ | BAC0 ✅ |
| Mode | Client (temporary) | Server (persistent) |
| Device ID | Auto (BAC0's own) | User-specified |
| Port | 47808 | 47808 (or 47809+) |
| Lifecycle | Start → Discover → Stop | Always running |
| Database | Store discovered devices | Store virtual devices |
| Network Role | Find devices | Be a device |

---

## ✨ Next Steps

1. **Clarify requirements** with company:
   - How many virtual devices?
   - Need custom points?
   - What data to expose?

2. **Create simple POC** (recommended):
   - Standalone Python script
   - One virtual device
   - Test discoverability

3. **Based on POC results**, decide:
   - Continue with BAC0 approach
   - Consider alternatives
   - Adjust architecture

4. **If successful**, proceed with Django integration

---

## 🔗 Quick Reference Links

- **BAC0 Docs:** https://bac0.readthedocs.io/
- **BAC0 GitHub:** https://github.com/ChristianTremblay/BAC0
- **Virtual Device Issue:** https://github.com/ChristianTremblay/BAC0/issues/146
- **Controller Guide:** https://bac0.readthedocs.io/en/latest/controller.html
- **PyPI Package:** https://pypi.org/project/BAC0/

---

**Research Completed:** October 7, 2025
**Current Branch:** `feat/simplified-bacnet-core`
**Current BAC0 Version:** 23.7.3 (confirmed in requirements.txt)
