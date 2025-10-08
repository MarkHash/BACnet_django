# Repository Cleanup & Branching Strategy

## 🎯 **Goal**
Transform the advanced BACnet application into a simplified version that meets company requirements while preserving all advanced work for portfolio purposes.

## 📋 **Current Situation**
- **Company Need**: Simple BACnet device discovery + manual device creation
- **Current State**: Advanced ML features (anomaly detection, energy analytics) that aren't needed
- **Missing Feature**: Manual device creation functionality

## 🌟 **Branching Strategy**

### **Branch 1: Portfolio Branch** 🎨
- **Name**: `feat/enhanced-anomaly-detection` (current branch)
- **Status**: **KEEP AS-IS** - Do not modify
- **Purpose**: Portfolio showcase, resume, interviews
- **Features**:
  - Multi-method ensemble anomaly detection (Z-score + IQR + Isolation Forest)
  - Energy analytics with ML forecasting
  - Advanced statistical analysis
  - Production-quality enterprise code architecture
  - Comprehensive documentation

### **Branch 2: Simplified Core** 🧹
- **Name**: `feat/simplified-bacnet-core`
- **Base**: Create from `main` or clean start
- **Purpose**: Company requirements - core functionality only
- **Features to KEEP**:
  - BACnet device discovery (WhoIs broadcasts)
  - Basic device management
  - Point discovery and cataloging
  - Simple data collection
  - Clean dashboard for device listing
- **Features to REMOVE**:
  - Energy analytics system (`energy_analytics.py`)
  - ML anomaly detection (`ml_utils.py`)
  - Advanced models (AlarmHistory, EnergyMetrics, BuildingEnergyForecast, SensorReadingStats, MaintenanceLog)
  - Complex API endpoints
  - Advanced dashboards and visualizations
  - ML dependencies (scikit-learn, pandas, numpy for ML)

### **Branch 3: Device Creation Feature** 🆕
- **Name**: `feat/manual-device-creation`
- **Base**: From `feat/simplified-bacnet-core`
- **Purpose**: Add missing manual device creation functionality
- **Features to ADD**:
  - Device creation form (web interface)
  - Manual device addition API
  - Device validation and management
  - Integration with existing discovery system

### **Branch 4: Final Company Version** 🎯
- **Name**: `feat/company-ready` (optional)
- **Base**: Merge `simplified-core` + `manual-device-creation`
- **Purpose**: Final deliverable for company
- **Result**: Clean, focused BACnet app with core functionality

## 📊 **Implementation Plan**

### **Phase 1: Create Simplified Branch**
1. Create `feat/simplified-bacnet-core` from appropriate base
2. Remove advanced features systematically:
   - Delete `energy_analytics.py`
   - Delete `ml_utils.py`
   - Remove advanced models from `models.py`
   - Clean up `api_views.py` (keep only device/discovery APIs)
   - Simplify `views.py` (remove complex dashboards)
   - Remove advanced templates
   - Update `urls.py` for simplified routing
   - Clean `requirements.txt` (remove ML dependencies)

### **Phase 2: Add Device Creation**
1. Create `feat/manual-device-creation` from simplified branch
2. Implement device creation functionality:
   - Device creation form template
   - Device creation view and validation
   - API endpoint for manual device addition
   - Integration with existing models
   - Admin interface improvements

### **Phase 3: Integration & Testing**
1. Merge device creation into simplified branch
2. Comprehensive testing of core functionality
3. Update documentation for simplified scope
4. Final cleanup and optimization

### **Phase 4: Documentation Update**
1. Create new README for simplified version
2. Update installation instructions
3. Focus documentation on core BACnet discovery
4. Remove references to advanced features

## 🎨 **Models Comparison**

### **Portfolio Version (Keep Everything)**
```python
- BACnetDevice ✅
- BACnetPoint ✅
- BACnetReading ✅
- DeviceStatusHistory ✅
- SensorReadingStats ✅ (ML stats)
- AlarmHistory ✅ (Anomaly alerts)
- MaintenanceLog ✅ (Advanced tracking)
- EnergyMetrics ✅ (HVAC analytics)
- BuildingEnergyForecast ✅ (ML forecasting)
```

### **Simplified Version (Core Only)**
```python
- BACnetDevice ✅ (Core device management)
- BACnetPoint ✅ (Device data points)
- BACnetReading ✅ (Basic data collection)
- DeviceStatusHistory ✅ (Simple connectivity)
- SensorReadingStats ❌ (Remove - ML stats)
- AlarmHistory ❌ (Remove - Complex alerts)
- MaintenanceLog ❌ (Remove - Advanced features)
- EnergyMetrics ❌ (Remove - Energy analytics)
- BuildingEnergyForecast ❌ (Remove - ML forecasting)
```

## 🏆 **Benefits of This Strategy**

### **For Portfolio/Resume**
- ✅ Preserved advanced ML work (ensemble anomaly detection)
- ✅ Shows energy analytics and statistical analysis skills
- ✅ Demonstrates enterprise code quality and architecture
- ✅ Comprehensive documentation and testing

### **For Company**
- ✅ Clean, maintainable codebase focused on their needs
- ✅ No unnecessary complexity or dependencies
- ✅ Faster performance without ML overhead
- ✅ Easier to understand and modify

### **For Development**
- ✅ Organized feature development in separate branches
- ✅ Clear separation of concerns
- ✅ Easy to track changes and progress
- ✅ Safe experimentation without affecting portfolio work

## 🚀 **Next Steps**

1. **Preserve Portfolio**: Ensure `feat/enhanced-anomaly-detection` is pushed to remote
2. **Create Simplified Branch**: Start with clean BACnet core functionality
3. **Remove Advanced Features**: Systematic cleanup of ML and analytics
4. **Add Device Creation**: Implement missing manual device creation
5. **Test & Document**: Ensure everything works and is well documented

## 📝 **Notes**

- **Portfolio branch should NEVER be modified** - it represents your advanced skills
- **Simplified branch is for company delivery** - focus on their specific needs
- **Keep commit history clean** in simplified branches for easy review
- **Document all changes** for easy handoff to company team

---

**Created**: October 2025
**Purpose**: Internship deliverable planning and portfolio preservation
**Status**: Ready for implementation