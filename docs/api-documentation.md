# API Documentation

This document provides comprehensive documentation for all BACnet Django API endpoints.

## API Overview

The application provides both modern class-based API views (v2) and legacy function-based endpoints for backward compatibility.

## Modern DRF API (v2) - Recommended

### Device Status API
**Endpoint**: `GET /api/v2/devices/status/`

Returns comprehensive device status overview with statistics.

**Response**:
```json
{
  "success": true,
  "summary": {
    "total_devices": 6,
    "online_devices": 4,
    "offline_devices": 1,
    "stale_devices": 1,
    "no_data_devices": 0
  },
  "devices": [
    {
      "device_id": 2000,
      "address": "192.168.1.100",
      "statistics": {
        "total_points": 161,
        "readable_points": 145,
        "points_with_values": 132,
        "device_status": "online",
        "last_reading_time": "2024-09-30T15:30:00Z"
      }
    }
  ],
  "timestamp": "2024-09-30T15:35:00Z"
}
```

### Device Trends API
**Endpoint**: `GET /api/v2/devices/{device_id}/trends/`

Returns historical data trends for device points over specified time periods.

**Parameters**:
- `period`: Time period (1hour, 6hours, 24hours, 7days, 30days)
- `points`: Comma-separated list of point identifiers (optional)

**Example**:
```bash
curl "http://127.0.0.1:8000/api/v2/devices/2000/trends/?period=24hours&points=analogInput:100,analogInput:101"
```

**Response**:
```json
{
  "success": true,
  "device_id": 2000,
  "period": "24hours",
  "points": [
    {
      "point_identifier": "analogInput:100",
      "readings": [
        {
          "timestamp": "2024-09-30T15:00:00Z",
          "value": 23.5
        }
      ],
      "statistics": {
        "min": 21.2,
        "max": 25.8,
        "avg": 23.4,
        "count": 288
      }
    }
  ]
}
```

### Device Performance API
**Endpoint**: `GET /api/v2/devices/performance/`

Returns performance metrics and activity analytics for all devices.

**Response**:
```json
{
  "success": true,
  "summary": {
    "total_devices": 6,
    "online_devices": 5,
    "total_readings": 15420,
    "avg_readings_per_device": 2570.0
  },
  "devices": [
    {
      "device_id": 2000,
      "address": "192.168.1.100",
      "total_readings": 3245,
      "readings_last_24h": 287,
      "avg_data_quality": 94.2,
      "most_active_point": "analogInput:100",
      "last_reading_time": "2024-09-30T15:30:00Z",
      "uptime_percentage": 98.5
    }
  ],
  "timestamp": "2024-09-30T15:35:00Z"
}
```

### Data Quality API
**Endpoint**: `GET /api/v2/devices/data-quality/`

Provides comprehensive data quality analysis including completeness, accuracy, freshness, and consistency metrics.

**Response**:
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
      "device_id": 2000,
      "address": "192.168.1.100",
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
          "last_reading_time": "2024-09-30T15:30:00Z",
          "data_gaps_hours": 1.5,
          "quality_score": 89.3
        }
      ],
      "data_coverage_percentage": 85.1,
      "avg_reading_interval_minutes": 5.2
    }
  ]
}
```

**Data Quality Metrics Explained**:
- **Completeness Score (0-100%)**: Percentage of expected readings present vs missing
- **Accuracy Score (0-100%)**: Percentage of readings without outliers (using IQR method)
- **Freshness Score (0-100%)**: How recent the latest readings are (exponential decay)
- **Consistency Score (0-100%)**: Regularity of reading intervals (low standard deviation = high score)
- **Overall Quality Score**: Weighted average (40% completeness, 30% accuracy, 20% freshness, 10% consistency)

### Anomaly Detection APIs

#### List Anomalies
**Endpoint**: `GET /api/v2/anomalies/`

**Parameters**:
- `hours`: Time range in hours (default: 24)
- `device_id`: Filter by specific device ID
- `anomalies_only`: Show only anomalous readings (true/false)
- `limit`: Maximum number of results (default: 100)

**Example**:
```bash
curl "http://127.0.0.1:8000/api/v2/anomalies/?anomalies_only=true&hours=24"
```

#### Device-Specific Anomalies
**Endpoint**: `GET /api/v2/anomalies/devices/{device_id}/`

Returns anomaly data for a specific device with same filtering options.

#### Anomaly Statistics
**Endpoint**: `GET /api/v2/anomalies/stats/`

**Parameters**:
- `days`: Time range in days for statistics (default: 7)

**Response**:
```json
{
  "success": true,
  "period_days": 7,
  "data": {
    "total_anomalies": 45,
    "anomalies_today": 8,
    "top_anomalies_devices": [
      {
        "point__device__device_id": 2000,
        "point__device__address": "192.168.1.100",
        "anomaly_count": 12
      }
    ],
    "anomaly_rate": 2.3
  }
}
```

### Energy Dashboard API
**Endpoint**: `GET /api/energy-dashboard/`

Returns comprehensive energy analytics including HVAC efficiency metrics, consumption estimates, and ML forecasts.

**Response**:
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

**Energy Analytics Metrics Explained**:
- **Estimated HVAC Load**: Energy consumption in kWh based on temperature deviation from 22°C comfort zone
- **Efficiency Score (0-100)**: HVAC performance based on stability (40%) + comfort (40%) + timing (20%)
- **Peak Demand Hour**: Hour with highest temperature deviation requiring most energy
- **Predicted Next Day Load**: ML forecast using linear regression with confidence scoring
- **Temperature Variance**: Statistical variance indicating HVAC stability performance

## Legacy API (v1) - Function-based

### Device Operations
- `POST /api/start-discovery/` - Start device discovery
- `POST /api/discover-points/{device_id}/` - Discover device points
- `POST /api/read-values/{device_id}/` - Read all point values from device
- `GET /api/device-values/{device_id}/` - Get current device values
- `POST /api/clear-devices/` - Clear all devices

### Point Operations
- `POST /api/read-point/{device_id}/{object_type}/{instance}/` - Read single point
- `GET /api/devices/status/` - Get device status (legacy format)
- `GET /api/devices/{device_id}/analytics/trends/` - Get device trends (legacy)

## API Features

### Authentication
Currently, the API does not require authentication for development. For production deployment, consider implementing:
- Token-based authentication
- Rate limiting per user
- API key management

### Rate Limiting
- Device Status API: 200 requests/hour
- Device Trends API: 100 requests/hour
- Other endpoints: 1000 requests/hour

### Error Handling
All API endpoints return structured error responses:
```json
{
  "success": false,
  "error": {
    "code": "DEVICE_NOT_FOUND",
    "message": "Device not found",
    "type": "DeviceNotFoundAPIError"
  },
  "timestamp": "2024-09-30T15:35:00Z"
}
```

### Response Size Guidelines
- `1hour`: ~11KB (ideal for real-time dashboards)
- `24hours`: ~338KB (good for daily views)
- `7days`: ~533KB (use with caution, consider pagination)

## Testing with PowerShell (Windows)

```powershell
# Test all main API endpoints
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v2/devices/status/" -Method GET
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v2/devices/performance/" -Method GET
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/energy-dashboard/" -Method GET

# Test POST endpoints
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/start-discovery/" -Method POST

# Get formatted JSON output
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v2/devices/performance/" -Method GET | ConvertTo-Json -Depth 5
```

## Interactive Documentation

- **Swagger UI**: http://127.0.0.1:8000/api/docs/
- **OpenAPI Schema**: http://127.0.0.1:8000/api/schema/

The Swagger UI provides interactive testing capabilities for all API endpoints with real-time parameter validation and response examples.