# BACnet Django Discovery Application

A Django web application for discovering, monitoring, and reading BACnet devices on your network. This application provides a user-friendly web interface for BACnet device discovery and real-time sensor data monitoring with optimized batch reading and PostgreSQL data persistence.

## Features

- **Automatic Device Discovery**: Broadcast WhoIs requests to discover BACnet devices
- **Point Discovery**: Read and catalog all BACnet objects from discovered devices
- **Optimized Batch Reading**: High-performance chunked batch reading with 3.7x speedup
- **Real-time Monitoring**: Read current sensor values from analog/binary points
- **Modern REST API**: Django REST Framework with auto-generated OpenAPI documentation
- **Interactive API Documentation**: Swagger UI for easy API testing and exploration
- **Web Dashboard**: Clean, responsive interface for device management
- **PostgreSQL Database**: Robust data persistence with proper indexing
- **Custom Exception Handling**: Professional error management and logging
- **Unit Conversions**: Automatic conversion of engineering units to display format
- **Admin Interface**: Django admin for advanced data management
- **Management Commands**: Database cleanup and maintenance utilities
- **Anomaly Detection**: Real-time statistical anomaly detection for temperature sensors

## Screenshots

### Dashboard
- Overview of all discovered devices
- Device status indicators (online/offline)
- Quick statistics (total devices, points, etc.)
- Discovery controls

### Device Details
- Detailed view of individual devices
- Real-time sensor readings with automatic refresh
- Point lists organized by object type
- Bulk sensor value reading

## Recent Improvements

### 🔧 **Windows Compatibility Fixes (Sept 2025)**
- **Fixed localhost binding issue**: Updated all documentation examples from `localhost:8000` to `127.0.0.1:8000` for Windows compatibility
- **Fixed IPv6/IPv4 resolution conflicts**: Resolved empty response errors when using `localhost` on Windows systems
- **Enhanced Docker configuration**: Proper Windows detection using `docker-compose.windows.yml` with `HOST_OS=Windows` environment variable
- **Eliminated server conflicts**: Windows integrated server now properly coordinates with Docker infrastructure

### 📊 **API Data Quality Improvements**
- **Fixed numpy data type errors**: Enhanced `DataQualityAPIView` to handle mixed numeric/text BACnet readings safely
- **Improved error handling**: Added robust filtering for non-numeric values in statistical calculations
- **Better data validation**: Prevents crashes when processing BACnet readings containing status text like "inactive", "offline"

### 🚀 **Performance & Architecture**
- **Optimized Windows architecture**: Windows integrated server handles BACnet operations while Docker provides database infrastructure
- **Improved API testing**: Native PowerShell `Invoke-RestMethod` examples for better Windows integration
- **Enhanced documentation**: All examples now use working URLs and proper Windows-specific configurations

### ✅ **Verified Working Features**
- DevicePerformanceAPIView: Real-time device performance metrics with 100% uptime tracking
- DataQualityAPIView: Comprehensive data quality analysis with accuracy, freshness, and consistency scoring
- POST endpoints: Device discovery and data collection operations working reliably
- Interactive API documentation: Swagger UI accessible at `http://127.0.0.1:8000/api/docs/`
- **Anomaly Detection System**: Z-score based anomaly detection for temperature sensors with automated scoring

## Requirements

- Python 3.12+
- Django 5.2+
- Django REST Framework 3.15.2+
- PostgreSQL 12+
- BAC0 library (23.07.03+)
- Bootstrap 5.1.3 (loaded via CDN)
- drf-spectacular (for OpenAPI documentation)

## Platform Support

This application now supports **cross-platform deployment** with automatic OS detection:

- **Linux/Mac**: Full Docker containerization with host networking
- **Windows**: Hybrid architecture with native BACnet networking

### Windows Support Features
- ✅ **Integrated Server Solution** - Single command deployment with `windows_integrated_server.py`
- ✅ **Native Windows networking** - Direct access to Windows network stack (192.168.1.x)
- ✅ **Automatic BACnet Operations** - Periodic discovery (30min) and data collection (5min)
- ✅ **Threading Architecture** - Web server + background BACnet worker in one process
- ✅ **Docker Infrastructure** - PostgreSQL and Redis in containers for reliability
- ✅ **Zero changes to Linux/Mac workflow** - existing deployments unchanged

### Quick Platform Comparison
| Feature | Linux/Mac | Windows |
|---------|-----------|---------|
| **Deployment** | `docker-compose up` | `docker-compose -f docker-compose.windows.yml up -d` + `python windows_integrated_server.py` |
| **BACnet Operations** | Docker container with host networking | Native Windows process |
| **Web Server** | Docker container | Native Windows process |
| **Database** | Docker container | Docker container |
| **Setup Complexity** | Single command | Two commands |
| **Network Access** | Host networking mode | Full Windows network stack |

## Installation

### Linux/Mac Installation (Docker)

### 1. Clone the repository
```bash
git clone <repository-url>
cd BACnet_django
```

### 2. Start with Docker Compose
```bash
docker-compose up -d
```

That's it! The application will be available at http://127.0.0.1:8000

### Windows Installation (Integrated Server)

### 1. Clone the repository
```bash
git clone <repository-url>
cd BACnet_django
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Start Docker infrastructure
```bash
docker-compose -f docker-compose.windows.yml up -d --build
```
This starts PostgreSQL, Redis, and Celery workers in Docker containers.

**⚠️ Important**: If you have local PostgreSQL installed, it may conflict with Docker PostgreSQL on port 5432. See [PostgreSQL Database Conflicts](#postgresql-database-conflicts) in Troubleshooting if data isn't being saved.

### 5. Run the integrated server
```bash
python windows_integrated_server.py
```

That's it! The integrated server combines:
- ✅ **Django web server** (port 8000)
- ✅ **Background BACnet worker** (native Windows networking)
- ✅ **Automatic periodic tasks** (device discovery + data collection)
- ✅ **Full database connectivity** (connects to Docker PostgreSQL)

### 6. Access the application
- Web Interface: http://127.0.0.1:8000/
- Admin Interface: http://127.0.0.1:8000/admin/

## How the Windows Integrated Server Works

### Single Process Architecture:
```
┌─────────────────────────────────────────┐
│               Windows Host              │
│                                         │
│  ┌─────────────────────────────────────┐│
│  │   windows_integrated_server.py     ││  ← Single Python Process
│  │                                     ││
│  │  [Main Thread]                      ││
│  │  • Django Web Server (port 8000)   ││  ← Web Interface
│  │  • HTTP Request Handling           ││  ← API Endpoints
│  │                                     ││
│  │  [Background Thread]                ││
│  │  • BACnet Device Discovery (1800s) ││  ← Native Windows Network
│  │  • Data Collection (300s)          ││  ← Direct UDP Access
│  │  • Error Handling & Recovery       ││  ← (192.168.1.x network)
│  └─────────────────────────────────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │          Docker Containers          ││
│  │  ┌─────────────────────────────────┐││
│  │  │ PostgreSQL Database (port 5432) │││  ← Data Persistence
│  │  └─────────────────────────────────┘││
│  │  ┌─────────────────────────────────┐││
│  │  │ Redis Cache (port 6379)         │││  ← Task Queue
│  │  └─────────────────────────────────┘││
│  │  ┌─────────────────────────────────┐││
│  │  │ Celery Workers (non-BACnet)     │││  ← Background Tasks
│  │  └─────────────────────────────────┘││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

### Key Benefits:
- **🚀 One Command**: `python windows_integrated_server.py` starts everything
- **🌐 Native Networking**: Full Windows network stack access for BACnet UDP
- **⚡ Real-time Operations**: Direct service calls, no queue delays
- **🔄 Auto-retry Logic**: Built-in error handling and recovery
- **📊 Live Monitoring**: Real-time status updates and logging
- **🐳 Docker Infrastructure**: Reliable database and caching services

## Configuration

### BAC0 Configuration

The application uses BAC0 for BACnet communication with automatic network detection. Key configuration options:

- **Automatic IP Detection**: BAC0 automatically detects network interface
- **Default Port**: UDP 47808 (BACnet standard)
- **Network Timeout**: 10 seconds for device discovery
- **Batch Size**: Maximum 50 points per batch read for optimal performance

### Django Settings

Key settings in `bacnet_project/settings.py`:

- **TIME_ZONE**: Set to your local timezone
- **DEBUG**: Set to False in production
- **ALLOWED_HOSTS**: Add your domain/IP for production
- **DATABASE**: PostgreSQL configuration with connection pooling

### Performance Settings

```python
# Optimized settings for BACnet operations
BACNET_CONSTANTS = {
    'MAX_BATCH_SIZE': 50,
    'REFRESH_THRESHOLD_SECONDS': 300,
    'MAX_READING_LIMIT': 50,
}
```

## Usage

### Discovering Devices

1. Navigate to the dashboard
2. Click "Start Discovery" to send WhoIs broadcasts
3. Discovered devices will appear in the devices list
4. Device status indicators show online/offline state

### Reading Device Points

1. Click device ID to view device details
2. If points haven't been discovered, click "🔍 Discover Points"
3. The application will discover all BACnet objects on the device
4. Points are organized by object type (analogInput, binaryInput, etc.)

### Reading Sensor Values

1. In device details, click "🌡️ Read Sensor Values"
2. Application uses optimized batch reading for better performance
3. Current values display with units and timestamps
4. Values automatically refresh every 30 seconds

### Data Management

```bash
# Clean database for fresh start
python manage.py clean_db

# Use Django admin for advanced data management
# Export data using Django admin
```

## API Endpoints

The application provides both legacy and modern REST API endpoints:

### Modern DRF API (v2) - Recommended
- `GET /api/v2/devices/status/` - Get comprehensive device status overview with statistics
- `GET /api/v2/devices/{device_id}/trends/` - Get historical trends and analytics for device points
- `GET /api/v2/devices/performance/` - Get device performance metrics and activity analytics
- `GET /api/v2/devices/data-quality/` - Get comprehensive data quality analysis for all devices
- `GET /api/v2/anomalies/` - List recent anomalies with filtering options
- `GET /api/v2/anomalies/devices/{device_id}/` - Get device-specific anomaly data
- `GET /api/v2/anomalies/stats/` - System-wide anomaly statistics and reporting
- `GET /api/energy-dashboard/` - **NEW** Energy analytics with HVAC efficiency metrics
- `GET /api/docs/` - Interactive Swagger UI documentation
- `GET /api/schema/` - OpenAPI schema for API documentation

**Features:**
- Auto-generated OpenAPI documentation
- Professional serialization and validation
- Consistent error handling with detailed responses
- Rate limiting (200/h for status, 100/h for trends)
- Query parameters for flexible data filtering
- Mixed data type support (numeric and text values handled safely)
- Robust statistics calculation excluding non-numeric values

**Example Usage:**
```bash
# Get all device status
curl "http://127.0.0.1:8000/api/v2/devices/status/"

# Get 24-hour trends for specific device
curl "http://127.0.0.1:8000/api/v2/devices/123/trends/?period=24hours"

# Get trends for specific points only
curl "http://127.0.0.1:8000/api/v2/devices/123/trends/?period=7days&points=analogInput:100,analogInput:101"

# PowerShell example with JSON formatting
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v2/devices/2000/trends?period=24hours" -Method GET | ConvertTo-Json -Depth 10
```

**Windows PowerShell Testing (Recommended):**
```powershell
# Test all main API endpoints
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v2/devices/status/" -Method GET
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v2/devices/performance/" -Method GET
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v2/devices/data-quality/" -Method GET

# Test POST endpoints
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/start-discovery/" -Method POST

# Get formatted JSON output
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v2/devices/performance/" -Method GET | ConvertTo-Json -Depth 5

# Check API health
(Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v2/devices/status/" -Method GET).success
```

**Response Size Guidelines:**
- `1hour`: ~11KB (ideal for real-time dashboards)
- `24hours`: ~338KB (good for daily views)
- `7days`: ~533KB (use with caution, consider pagination)
- For frontend: Recommend 24-hour default with optional historical data

```bash
# Get device performance analytics
curl "http://127.0.0.1:8000/api/v2/devices/performance/"

# Get data quality analysis for all devices
curl "http://127.0.0.1:8000/api/v2/devices/data-quality/"

# Get energy analytics dashboard data
curl "http://127.0.0.1:8000/api/energy-dashboard/"
```

**Device Performance API Response:**
```json
{
  "success": true,
  "summary": {
    "total_active_devices": 6,
    "total_readings": 2153,
    "avg_uptime_percentage": 95.2
  },
  "devices": [
    {
      "device_id": 123,
      "address": "192.168.1.5",
      "total_readings": 456,
      "readings_last_24h": 89,
      "avg_data_quality": 98.5,
      "most_active_point": "analogInput:100",
      "last_reading_time": "2024-01-15T10:30:00Z",
      "uptime_percentage": 96.8
    }
  ],
  "timestamp": "2024-01-15T10:35:00Z"
}
```

**Data Quality API Response:**
```json
{
  "success": true,
  "summary": {
    "completeness_score": 85.4,
    "accuracy_score": 96.2,
    "freshness_score": 78.9,
    "consistency_score": 82.1,
    "overall_quality_score": 87.3
  },
  "devices": [
    {
      "device_id": 123,
      "address": "192.168.1.5",
      "metrics": {
        "completeness_score": 88.2,
        "accuracy_score": 98.5,
        "freshness_score": 92.1,
        "consistency_score": 85.7,
        "overall_quality_score": 91.4
      },
      "point_quality": [
        {
          "point_identifier": "analogInput:100",
          "total_readings": 245,
          "missing_readings": 43,
          "outlier_count": 2,
          "last_reading_time": "2024-01-15T10:30:00Z",
          "data_gaps_hours": 1.5,
          "quality_score": 89.3
        }
      ],
      "data_coverage_percentage": 85.1,
      "avg_reading_interval_minutes": 5.2
    }
  ],
  "timestamp": "2024-01-15T10:35:00Z"
}
```

**Data Quality Metrics Explained:**
- **Completeness Score (0-100%)**: Percentage of expected readings present vs missing
- **Accuracy Score (0-100%)**: Percentage of readings without outliers (using IQR method)
- **Freshness Score (0-100%)**: How recent the latest readings are (exponential decay)
- **Consistency Score (0-100%)**: Regularity of reading intervals (low standard deviation = high score)
- **Overall Quality Score**: Weighted average (40% completeness, 30% accuracy, 20% freshness, 10% consistency)

**Energy Dashboard API Response:**
```json
{
  "success": true,
  "data": {
    "total_devices": 6,
    "devices_with_energy_data": 4,
    "total_energy_consumed": 127.45,
    "average_efficiency_score": 78.5,
    "devices": [
      {
        "device_id": 2000,
        "device_address": "192.168.1.100",
        "date": "2024-09-30",
        "avg_temperature": 23.2,
        "min_temperature": 21.8,
        "max_temperature": 24.7,
        "temperature_variance": 0.85,
        "estimated_hvac_load": 15.8,
        "peak_demand_hour": 14,
        "efficiency_score": 82.3,
        "predicted_next_day_load": 16.2,
        "confidence_score": 0.87
      }
    ],
    "trends": [
      {"hour": 0, "energy": 12.5},
      {"hour": 1, "energy": 11.8},
      {"hour": 14, "energy": 18.9},
      {"hour": 23, "energy": 13.2}
    ]
  },
  "timestamp": "2024-09-30T15:30:00Z"
}
```

**Energy Analytics Metrics Explained:**
- **Estimated HVAC Load**: Energy consumption in kWh based on temperature deviation from 22°C comfort zone
- **Efficiency Score (0-100)**: HVAC performance based on stability (40%) + comfort (40%) + timing (20%)
- **Peak Demand Hour**: Hour with highest temperature deviation requiring most energy
- **Predicted Next Day Load**: ML forecast using linear regression with confidence scoring
- **Temperature Variance**: Statistical variance indicating HVAC stability performance

### Legacy API (v1) - Function-based
- `POST /api/start-discovery/` - Start device discovery
- `POST /api/discover-points/{device_id}/` - Discover device points
- `POST /api/read-values/{device_id}/` - Read all point values from device
- `POST /api/read-point/{device_id}/{object_type}/{instance}/` - Read single point
- `GET /api/device-values/{device_id}/` - Get current device values
- `POST /api/clear-devices/` - Clear all devices

## Database Models

### BACnetDevice
- Device ID, IP address, vendor information
- Online status and timestamps
- Point reading status
- Soft delete with `is_active` field

### BACnetPoint
- Object type, instance number, identifier
- Present value, units, object name
- Data type and readability flags
- Foreign key to device

### BACnetReading
- Historical sensor readings with anomaly detection
- Timestamps and quality indicators
- Anomaly scores and flags for statistical analysis
- Linked to specific points

### DeviceStatusHistory
- Device online/offline history
- Status change timestamps

## Architecture

### Components

1. **Django Views** (`discovery/views.py`)
   - Web interface and API endpoints
   - Device and point management
   - Error handling with custom exceptions

2. **BACnet Service** (`discovery/services.py`)
   - BAC0 integration with context managers
   - Optimized batch reading with chunking
   - Professional error handling
   - Connection lifecycle management

3. **Models** (`discovery/models.py`)
   - PostgreSQL-optimized database schema
   - Data validation and relationships
   - Soft delete patterns

4. **Constants** (`discovery/constants.py`)
   - BACnet property names
   - Readable object types
   - Unit conversion mappings

5. **Custom Exceptions** (`discovery/exceptions.py`)
   - Structured error hierarchy
   - BACnet-specific error types

6. **Templates** (`discovery/templates/`)
   - Responsive web interface
   - Bootstrap-based design
   - Real-time updates via JavaScript

### BACnet Communication

- Uses BAC0 library (Lite mode) for BACnet protocol support
- Supports BACnet/IP over Ethernet
- Handles WhoIs/IAm for device discovery
- ReadProperty and ReadMultiple requests for data collection
- Context manager pattern for automatic connection management
- Chunked batch reading for large devices (161+ points)

### Performance Optimizations

- **Batch Reading**: ReadMultiple requests with up to 50 points per batch
- **Chunked Processing**: Large devices split into manageable chunks
- **Connection Pooling**: Efficient BAC0 connection management
- **Database Indexing**: Optimized PostgreSQL indexes
- **Error Recovery**: Graceful fallback to individual reads on batch failures

## Anomaly Detection System

The application includes real-time anomaly detection for temperature sensors using statistical analysis methods.

### Features

- **Ensemble Detection**: Z-score + IQR methods working together for robust anomaly detection
- **Z-Score Detection**: Statistical anomaly detection using standard deviation analysis
- **IQR Detection**: Interquartile Range method resistant to outliers
- **Temperature Sensor Focus**: Automatically detects and analyzes temperature readings (°C, °F)
- **Real-time Processing**: Anomaly detection runs during data collection
- **Historical Analysis**: Uses 24-hour rolling window for statistical baseline
- **Data Filtering**: Automatic exclusion of invalid readings (0.0°C values)
- **Configurable Thresholds**: Adjustable Z-score threshold (default: 2.5 standard deviations)

### How It Works

1. **Automatic Detection**: Temperature sensors identified by units containing "degree"
2. **Data Filtering**: Invalid readings (0.0°C) excluded from statistical analysis
3. **Historical Analysis**: Each new reading compared against 24-hour historical data
4. **Ensemble Detection**:
   - **Z-Score**: `z_score = |new_value - mean| / std_deviation`
   - **IQR**: Detects outliers using quartile ranges (Q1, Q3)
5. **Anomaly Flagging**: Reading flagged if EITHER method detects anomaly
6. **Database Storage**: Z-score and anomaly flag stored with each reading

### Implementation Details

```python
# Core anomaly detection in ml_utils.py
class AnomalyDetector:
    def __init__(self, z_score_threshold=2.5):
        self.z_score_threshold = z_score_threshold

    def detect_z_score_anomaly(self, point, new_value):
        # Z-score statistical analysis
        # Returns z_score value

    def detect_iqr_anomaly(self, point, new_value):
        # IQR outlier detection
        # Returns (iqr_score, is_anomaly)

# Ensemble detection in services.py
def _detect_anomaly_if_temperature(self, point, value_str):
    z_score = self.anomaly_detector.detect_z_score_anomaly(point, numeric_value)
    iqr_score, iqr_is_anomaly = self.anomaly_detector.detect_iqr_anomaly(point, numeric_value)
    combined_is_anomaly = (z_score > threshold) or iqr_is_anomaly
    return z_score, iqr_score, combined_is_anomaly
```

### Integration Points

- **services.py:60** - AnomalyDetector instantiated in BACnetService
- **services.py:411-424** - Temperature sensor detection and analysis
- **services.py:435, 501** - Anomaly detection during data collection
- **Database Fields** - `anomaly_score` and `is_anomaly` in BACnetReading model

### Current Status

**✅ Active Features:**
- **Ensemble Anomaly Detection**: Z-score + IQR methods working together for robust detection
- **Data Filtering**: Automatic exclusion of 0.0°C readings from statistical analysis
- **Real-time Processing**: Anomaly detection during data collection with ensemble scoring
- **Comprehensive API Suite**: REST endpoints for anomaly querying and statistics
- **Database Storage**: Anomaly scores and flags stored with each reading
- **106k+ Historical Readings**: Migrated with anomaly data for analysis

**📊 Recent Achievements (Sept 2025):**
- **Database Migration Success**: 106k readings with 34k+ anomaly scores migrated to Docker PostgreSQL
- **Ensemble Detection**: Z-score + IQR methods provide complementary anomaly detection
- **API Endpoints**: Complete REST API suite for anomaly data access
- **Production Testing**: Comprehensive test framework with multiple detection scenarios
- **Database Connectivity**: Resolved PostgreSQL conflicts between local and Docker instances

**🚀 API Endpoints Available:**
- `GET /api/v2/anomalies/` - List all anomalies with filtering
- `GET /api/v2/anomalies/devices/{id}/` - Device-specific anomaly data
- `GET /api/v2/anomalies/stats/` - System-wide anomaly statistics
- **OpenAPI Documentation**: Available at `/api/docs/` with Swagger UI

**🔄 Planned Enhancements:**
- Moving Average detection for trend analysis
- Isolation Forest ML method for advanced detection
- Alert system integration with AlarmHistory model
- Dashboard views for anomaly visualization

### Configuration

```python
# Default settings
Z_SCORE_THRESHOLD = 2.5        # Standard deviations for anomaly detection
LOOKBACK_HOURS = 24            # Historical data window
MIN_READINGS = 5               # Minimum readings for statistical analysis
```

### Database Schema

```sql
-- BACnetReading table includes anomaly detection fields
ALTER TABLE discovery_bacnetreading ADD COLUMN anomaly_score FLOAT NULL;
ALTER TABLE discovery_bacnetreading ADD COLUMN is_anomaly BOOLEAN DEFAULT FALSE;
```

### Example Usage

```python
# Check recent anomalies
from discovery.models import BACnetReading

anomalous_readings = BACnetReading.objects.filter(
    is_anomaly=True,
    read_time__gte=timezone.now() - timedelta(hours=24)
)

# Temperature sensors with anomaly detection
temp_sensors = BACnetPoint.objects.filter(
    units__icontains='degree'
)
```

### API Usage Examples

```bash
# Get all anomalies from last 24 hours
curl "http://localhost:8000/api/v2/anomalies/?anomalies_only=true"

# Get anomalies for specific device
curl "http://localhost:8000/api/v2/anomalies/devices/2000/?anomalies_only=true"

# Get system-wide anomaly statistics
curl "http://localhost:8000/api/v2/anomalies/stats/"

# Get anomaly statistics for last 30 days
curl "http://localhost:8000/api/v2/anomalies/stats/?days=30"
```

### Test Framework

```bash
# Run comprehensive anomaly detection tests
python test_anomaly_detection.py

# Example output:
# Normal reading  |   29.0°C | Z-score:   0.55 | IQR:   0.31 | ✅ Normal
# High anomaly    |   45.0°C | Z-score:  16.36 | IQR:   6.46 | 🚨 ANOMALY
```

## Troubleshooting

### Platform-Specific Issues

#### Windows-Specific Issues

1. **"Windows detected but no BACnet devices found"**
   - Verify your Windows machine can reach BACnet devices:
     ```bash
     ping 192.168.1.5  # Replace with your BACnet device IP
     ```
   - Check Windows firewall settings for UDP port 47808
   - Ensure you're on the same subnet as BACnet devices

2. **"Double BACnet connection error"**
   - Fixed in current version with connection reuse
   - If you see this error, restart Django server

3. **Docker port conflicts**
   - Make sure you're using `docker-compose.windows.yml`
   - Don't run both `docker-compose.yml` and `docker-compose.windows.yml` simultaneously

**🗄️ PostgreSQL Database Conflicts**
   - **Issue**: Windows service can't save data to Docker database
   - **Cause**: Local PostgreSQL service using port 5432 (conflicts with Docker PostgreSQL)
   - **Check**: `netstat -an | findstr ":5432"` (should show only Docker connections)
   - **Solution**: Stop local PostgreSQL service:
     ```bash
     # As Administrator:
     net stop postgresql-x64-15
     # Or use Services Manager (services.msc)
     ```
   - **Verification**: Test database connection:
     ```bash
     psql -h localhost -U bacnet_user -d bacnet_django -c "SELECT 1;"
     ```
   - **Note**: New machines without local PostgreSQL work immediately

4. **"Empty reply from server" or "localhost:8000 not working"** ✅ **FIXED**
   - **Solution**: Use `127.0.0.1:8000` instead of `localhost:8000`
   - **Root cause**: Windows resolves `localhost` to IPv6 (`::1`) but server binds to IPv4 only
   - **All documentation updated**: Examples now use `127.0.0.1:8000`

5. **"net::ERR_EMPTY_RESPONSE" on API calls** ✅ **FIXED**
   - **Solution**: Ensure Windows integrated server is running: `python windows_integrated_server.py`
   - **Solution**: Use correct docker-compose file: `docker-compose -f docker-compose.windows.yml up -d`
   - **Verification**: Check API works with `Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v2/devices/status/"`

6. **DataQualityAPIView numpy errors** ✅ **FIXED**
   - **Error**: `ufunc 'subtract' did not contain a loop with signature matching types`
   - **Solution**: Enhanced data filtering to handle mixed numeric/text BACnet readings
   - **Now handles**: "inactive", "offline", and other status text values safely

#### Linux/Mac-Specific Issues

1. **Docker BACnet worker not finding devices**
   - Check host networking is working: `docker run --rm --net=host busybox ip addr`
   - Verify no firewall blocking UDP 47808

### Common Issues (All Platforms)

1. **No devices discovered**
   - Check network connectivity and subnet
   - Verify firewall settings for UDP port 47808
   - Ensure BACnet devices are accessible
   - **Windows**: Make sure Django is running natively (not in Docker)
   - **Linux/Mac**: Make sure Docker has host networking access

2. **PostgreSQL connection errors**
   - Verify your `.env` file exists and has correct credentials
   - Test connection with your credentials from `.env`:
     ```bash
     # Use your actual credentials from .env file
     psql -h localhost -U your_db_user -d bacnet_django
     ```
   - **Docker users**: Ensure containers are running: `docker-compose ps`
   - Check PostgreSQL service is running: `sudo systemctl status postgresql` (Linux)
   - Ensure database and user exist:
     ```sql
     # Connect as postgres user
     psql -U postgres
     \l  -- List databases (should show bacnet_django)
     \du -- List users (should show your user)
     ```
   - Verify `.env` file is loaded correctly:
     ```bash
     python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('DB_USER:', os.getenv('DB_USER'))"
     ```

3. **Platform detection issues**
   - Check the startup message:
     - Windows: "🪟 Windows detected: BACnet worker will run natively"
     - Linux/Mac: "🐧 Linux/Mac detected: Using Docker BACnet worker"
   - If incorrect, check `platform.system()` output:
     ```python
     import platform
     print(platform.system())  # Should be 'Windows', 'Linux', or 'Darwin'
     ```

4. **Point reading failures**
   - Some devices may have security restrictions
   - Check device documentation for supported properties
   - Verify device is online and responsive

5. **Performance issues**
   - Monitor batch read success in logs
   - Check network latency to devices
   - Consider adjusting MAX_BATCH_SIZE

### Debug Information

- Enable Django debug mode in settings.py
- Check application logs for BACnet communication
- Use Django admin to inspect database records
- Monitor performance with batch read statistics

### Logging

```python
# Key loggers to monitor:
- discovery.services    # BACnet operations
- discovery.views      # Web interface
- BAC0_Root            # BAC0 library (set to WARNING)
```

## Development

### Project Structure
```
BACnet_django/
├── bacnet_project/          # Django project settings
├── discovery/               # Main application
│   ├── migrations/         # Database migrations
│   ├── templates/          # HTML templates
│   ├── management/         # Custom management commands
│   ├── models.py          # Database models
│   ├── views.py           # Web views and API
│   ├── services.py        # BACnet communication service
│   ├── constants.py       # BACnet constants and mappings
│   ├── exceptions.py      # Custom exception hierarchy
│   └── urls.py           # URL routing
├── requirements.txt        # Python dependencies
├── manage.py              # Django management script
├── .env                   # Environment variables (create from .env.example)
├── .env.example          # Environment variables template
└── README.md             # This file
```

### Management Commands

```bash
# Clean database for fresh start
python manage.py clean_db

# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser
```

### Testing

```bash
# Run tests
python manage.py test

# Test with logging
python manage.py runserver 2>&1 | tee test_log.txt
```

### Adding Features

1. **New BACnet Properties**
   - Extend `services.py` to read additional properties
   - Update models to store new data
   - Add constants to `constants.py`

2. **Additional Device Types**
   - Update device discovery logic in `services.py`
   - Add support for new object types in constants
   - Extend admin interface

3. **Performance Monitoring**
   - Add metrics collection
   - Implement performance dashboards
   - Monitor batch read efficiency

## Production Deployment

### Database Configuration
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'MAX_CONNS': 20,
        }
    }
}
```

### Environment Variables
```bash
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=your-domain.com,your-ip-address
DB_NAME=bacnet_production
DB_USER=bacnet_user
DB_PASSWORD=secure-password
```

### Security Checklist
- Change SECRET_KEY in production
- Set DEBUG = False
- Configure proper ALLOWED_HOSTS
- Use environment variables for sensitive data
- Implement authentication for admin access
- Consider network segmentation for BACnet traffic
- Regular database backups

## Performance Metrics

Based on testing with real BACnet devices:

- **Device Discovery**: 3 devices discovered in ~9 seconds
- **Point Discovery**: 161+ points discovered in ~1.5 seconds
- **Batch Reading**: 3.7x faster than individual reads
  - Individual reads: 3.82s for 28 points
  - Batch reads: 1.03s for 28 points
- **Large Device Handling**: 161+ points read in ~4 batches
- **Database Performance**: PostgreSQL with optimized indexes

## Celery Integration

For parallel device processing (already configured):

```python
# Celery is already installed and configured in settings.py
# Current configuration uses PostgreSQL as broker and result backend:

CELERY_BROKER_URL = 'sqlalchemy+postgresql://bacnet_user:password@localhost:5432/bacnet_django'
CELERY_RESULT_BACKEND = 'db+postgresql://bacnet_user:password@localhost:5432/bacnet_django'

# Scheduled tasks configured:
CELERY_BEAT_SCHEDULE = {
    'calculate-hourly-stats': {
        'task': 'discovery.tasks.calculate_hourly_stats',
        'schedule': crontab(minute=0),  # Every hour
    },
    'calculate-daily-stats': {
        'task': 'discovery.tasks.calculate_daily_stats',
        'schedule': crontab(hour=0, minute=5),  # Daily at 00:05
    },
}
```

**To start Celery services:**
```bash
# Start Celery worker
celery -A bacnet_project worker --loglevel=info

# Start Celery beat (scheduler)
celery -A bacnet_project beat --loglevel=info
```

## License

[Add your license information here]

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## Support

For issues and questions:
- Create GitHub issues for bugs and feature requests
- Check logs for BACnet communication issues
- Review troubleshooting section for common problems

## Files Added for Windows Support

For reference, these are the minimal files added to enable Windows support:

### New Files
- `docker-compose.windows.yml` - Windows-specific Docker configuration (excludes web service)

### Modified Files
- `bacnet_project/settings.py` - Added OS auto-detection (5 lines at end)
- `discovery/services.py` - Fixed BACnet connection reuse in `__enter__` method

### How It Works
- **Web interface already calls BACnetService directly** - no additional workers needed
- **Django runs natively on Windows** - gets real network access (192.168.1.x)
- **Database/Redis run in containers** - reliable infrastructure services
- **Automatic platform detection** - no user configuration required

### Architecture Benefits
- **Zero risk**: Linux/Mac behavior unchanged
- **Minimal changes**: ~10 lines of code modifications
- **Simple**: No trigger files or background workers needed
- **Direct**: Web interface → BACnetService → Windows network
- **Maintainable**: Shared business logic across platforms

## Changelog

### Version 2.4 (Current) - Enterprise Code Architecture & Energy Analytics
- **🏗️ Enterprise Code Refactoring**: Complete separation of concerns with `api_views.py` module
- **⚡ Energy Analytics Pipeline**: Advanced HVAC energy consumption analysis and forecasting
- **📊 Energy Dashboard**: Interactive web dashboard with real-time metrics and charts
- **🤖 ML Forecasting**: Linear regression forecasting for next-day energy consumption
- **📈 Efficiency Scoring**: HVAC efficiency analysis based on temperature control performance
- **🔧 Production-Ready Codebase**: 100% type hints, comprehensive exception handling, Flake8 compliance
- **📚 Professional Documentation**: Complete module docstrings and enterprise-level code organization

#### Code Architecture Improvements
- **Separation of Concerns**: Created dedicated `api_views.py` for all class-based API endpoints
- **Type Safety**: Added comprehensive type hints across all modules (`energy_analytics.py`, `ml_utils.py`, `views.py`)
- **Exception Handling**: Custom exception hierarchy with graceful error recovery
- **Code Quality**: Flake8 compliance with proper import organization and line length standards
- **Method Refactoring**: Broke down large methods into focused, single-responsibility functions
- **Documentation**: Professional module-level docstrings explaining architecture and functionality

#### Energy Analytics Features
- **HVAC Load Estimation**: Temperature deviation-based energy consumption calculations
- **Efficiency Scoring**: Multi-factor scoring (stability 40% + comfort 40% + timing 20%)
- **ML Forecasting**: Linear regression with confidence scoring for next-day predictions
- **Interactive Dashboard**: Chart.js integration with gradient metric cards and responsive design
- **Data Pipeline**: Automated daily metrics calculation with database persistence
- **Performance Optimization**: Efficient database queries with data coverage ratio calculations

#### Technical Implementation
- **Energy Metrics Model**: New database table for storing daily energy analytics
- **Constants Integration**: Centralized energy calculation constants in `constants.py`
- **API Endpoints**: RESTful energy dashboard API with JSON data provisioning
- **Frontend Integration**: Modern API-first architecture with JavaScript data loading
- **Production Testing**: Verified with real September 2024 temperature data (200K+ readings)

### Version 2.3 - Anomaly Detection Integration
- **Real-time Anomaly Detection**: Z-score based statistical anomaly detection for temperature sensors
- **Intelligent Sensor Detection**: Automatic identification of temperature sensors by units (°C, °F)
- **Historical Analysis**: 24-hour rolling window for statistical baseline calculation
- **Database Integration**: Anomaly scores and flags stored with each reading
- **ML Utils Module**: Extensible framework for additional detection algorithms
- **Test Validation**: Verified with 79 temperature sensors and real BACnet data
- **Smart Filtering**: Handles mixed data types and non-numeric values safely

### Version 2.2 - Django REST Framework Integration
- Added Django REST Framework with professional class-based API views
- Created comprehensive serializers for data validation and documentation
- Implemented auto-generated OpenAPI documentation with Swagger UI
- Added modern v2 API endpoints with rate limiting and error handling
- **Device Performance Analytics API**: Real-time device activity monitoring and performance metrics
- **Data Quality Monitoring API**: Comprehensive data quality analysis with completeness, accuracy, freshness, and consistency metrics
- Maintained backward compatibility with legacy function-based API endpoints
- Enhanced API features: query parameters, pagination, and structured responses

### Version 2.1 - Windows Support
- Added cross-platform support with automatic OS detection
- Implemented hybrid architecture for Windows (native BACnet + containerized services)
- Fixed BACnet connection reuse issues
- Zero changes to existing Linux/Mac functionality
- Created Windows-specific Docker Compose configuration

### Version 2.0
- Migrated from BACpypes to BAC0
- Implemented PostgreSQL database
- Added optimized batch reading
- Custom exception handling
- Context manager pattern
- Unit conversion system
- Performance improvements (3.7x faster)

### Version 1.0
- Initial release with BACpypes
- SQLite database
- Basic device discovery
- Individual point reading
