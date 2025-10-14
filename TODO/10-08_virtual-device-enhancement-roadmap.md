# Virtual Device Enhancement Roadmap
**Date:** October 8, 2025
**Priority:** Medium-High (for portfolio showcase)

## Current Limitations to Address

### 1. Broadcast Discovery Response
**Issue**: Virtual devices don't respond to `WhoIs` broadcasts
**Impact**: Not discoverable by standard BACnet scanners
**Solution Required**: Implement proper BACnet device with broadcast response capability

### 2. Controllable BACnet Objects
**Issue**: Only device object exists, no points to read/write
**Impact**: Cannot demonstrate real BACnet functionality
**Solution Required**: Add analog inputs, analog outputs, binary inputs, binary outputs

### 3. Value Modification
**Issue**: No writable properties for testing control operations
**Impact**: Cannot simulate realistic building automation scenarios
**Solution Required**: Implement writable object properties

## Enhancement Plan

### Phase 1: Enhanced Device Discovery (High Priority)

#### 1.1 Implement Full BACnet Device
**File**: `discovery/management/commands/run_virtual_devices.py`
**Changes**:
- Replace `BAC0.lite()` with full `BAC0.start()` or custom device
- Configure proper BACnet device with WhoIs response
- Add device identification properties (vendor name, model, firmware)

**Implementation**:
```python
# Instead of: bacnet = BAC0.lite(deviceId=device.device_id, port=device.port)
# Use: Full device with object definitions
device_config = {
    'deviceId': device.device_id,
    'deviceName': device.device_name,
    'vendorId': 999,  # Custom vendor ID
    'vendorName': 'Django BACnet Virtual',
    'modelName': 'Virtual Device',
    'firmwareRevision': '1.0'
}
```

#### 1.2 Configure Broadcast Response
**Research Required**: BAC0 documentation for enabling WhoIs broadcast response
**Testing**: Verify device appears in `bacnet.discover()` results

### Phase 2: BACnet Objects and Points (High Priority)

#### 2.1 Add Virtual Points Model
**File**: `discovery/models.py`
**New Model**: `VirtualBACnetPoint`
```python
class VirtualBACnetPoint(models.Model):
    device = models.ForeignKey(VirtualBACnetDevice, on_delete=models.CASCADE)
    object_type = models.CharField(max_length=20)  # AI, AO, BI, BO
    object_instance = models.IntegerField()
    object_name = models.CharField(max_length=100)
    present_value = models.FloatField(default=0.0)
    units = models.CharField(max_length=50, default='noUnits')
    writable = models.BooleanField(default=False)
```

#### 2.2 Point Management Interface
**Files**: Templates and views for point CRUD
- `virtual_device_detail.html`: Show device with its points
- Point creation/editing forms
- AJAX updates for real-time value changes

#### 2.3 Integrate Points with BAC0 Device
**Implementation**: Create BACnet objects for each virtual point
```python
# Analog Input example
device.add_object(AnalogInputObject(
    objectIdentifier=('analogInput', point.object_instance),
    objectName=point.object_name,
    presentValue=point.present_value,
    units=point.units
))
```

### Phase 3: Value Control and Monitoring (Medium Priority)

#### 3.1 Real-time Value Updates
**Feature**: Web interface to change point values
**Technology**: WebSocket or polling for live updates
**Implementation**:
- AJAX endpoints for value updates
- Update both database and BAC0 device object
- Reflect changes to BACnet clients

#### 3.2 Point Simulation
**Feature**: Automatic value simulation (temperature drift, schedules)
**Use Cases**:
- Temperature sensors with random variation
- Occupancy sensors with time-based patterns
- Equipment status cycling

#### 3.3 Command Priority Arrays
**Feature**: Implement BACnet priority arrays for outputs
**Purpose**: Demonstrate proper BACnet control hierarchies

### Phase 4: Advanced Features (Low Priority)

#### 4.1 Object Templates
**Feature**: Pre-configured point sets for common devices
**Templates**:
- HVAC Controller (Temperature, Humidity, Damper Position)
- Lighting Controller (Switch Status, Dimmer Level)
- Energy Meter (Power, Energy, Voltage, Current)

#### 4.2 Trending and COV
**Feature**: Change of Value notifications
**Implementation**: Automatic notifications when values change
**Testing**: Verify COV subscriptions work with external clients

#### 4.3 Alarm and Event Objects
**Feature**: BACnet alarm/event handling
**Use Cases**: High/low limit alarms, equipment fault simulation

## Technical Implementation Notes

### BAC0 Library Research Required
1. **Full Device Creation**: Documentation for creating devices with custom objects
2. **Object Factories**: How to add analog/binary inputs/outputs
3. **Property Handling**: Implementing writable properties
4. **Broadcast Configuration**: Ensuring WhoIs response capability

### Database Migrations
- Add VirtualBACnetPoint model
- Relationship between devices and points
- Default point sets for new devices

### API Enhancements
- Endpoints for point value updates
- Real-time monitoring endpoints
- Bulk point creation/import

### Testing Strategy
1. **Unit Tests**: Point CRUD operations
2. **Integration Tests**: BAC0 device creation with points
3. **BACnet Protocol Tests**: External client communication
4. **Performance Tests**: Multiple devices with many points

## Success Metrics

### Phase 1 Success
- ✅ Virtual devices appear in `bacnet.discover()`
- ✅ External BACnet tools can find devices
- ✅ Device properties readable via standard BACnet clients

### Phase 2 Success
- ✅ Virtual devices have controllable points
- ✅ Web interface shows and edits point values
- ✅ BACnet clients can read point values

### Phase 3 Success
- ✅ Real-time value updates via web interface
- ✅ Value changes reflected to BACnet clients
- ✅ Proper priority array handling for outputs

## Portfolio Value

### Demonstrable Skills
1. **BACnet Protocol**: Deep understanding of building automation
2. **Real-time Systems**: WebSocket/polling implementations
3. **Database Design**: Complex relationships and data modeling
4. **API Design**: RESTful endpoints for device control
5. **Frontend Integration**: Real-time monitoring interfaces

### Industry Relevance
- Building automation systems
- IoT device simulation
- Industrial protocol implementation
- Real-time monitoring dashboards

## Development Time Estimates

- **Phase 1**: 2-3 days (broadcast discovery)
- **Phase 2**: 5-7 days (points and objects)
- **Phase 3**: 3-4 days (real-time control)
- **Phase 4**: 5-10 days (advanced features)

**Total**: 15-24 days for full implementation

## Immediate Next Steps

1. **Research BAC0 documentation** for full device implementation
2. **Create Phase 1 implementation plan** with specific code changes
3. **Set up testing environment** for external BACnet client validation
4. **Design VirtualBACnetPoint model** schema
5. **Create development branch** for enhanced virtual devices