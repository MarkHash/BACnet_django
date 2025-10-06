# API Documentation

This document provides documentation for the simplified BACnet Django API endpoints.

## API Overview

The application provides simple REST API endpoints for core BACnet functionality including device management, data collection, and basic monitoring.

## Core API Endpoints

### Device Status API
**Endpoint**: `GET /api/devices/status/`

Returns overview of all active BACnet devices with basic statistics.

**Response**:
```json
{
  "success": true,
  "summary": {
    "total_devices": 3,
    "online_devices": 2,
    "offline_devices": 1,
    "stale_devices": 0,
    "no_data_devices": 0
  },
  "devices": [
    {
      "device_id": 2000,
      "address": "192.168.1.100",
      "statistics": {
        "total_points": 45,
        "readable_points": 40,
        "points_with_values": 35,
        "device_status": "online",
        "last_reading_time": "2024-10-06T15:30:00Z"
      }
    }
  ],
  "timestamp": "2024-10-06T15:35:00Z"
}
```

### Device Trends API
**Endpoint**: `GET /api/devices/{device_id}/trends/`

Returns historical data trends for device points over specified time periods.

**Parameters**:
- `period`: Time period (1hour, 6hours, 24hours, 7days, 30days)
- `points`: Comma-separated list of point identifiers (optional)

**Example**:
```bash
curl "http://127.0.0.1:8000/api/devices/2000/trends/?period=24hours&points=analogInput:100"
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
          "timestamp": "2024-10-06T15:00:00Z",
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

## Device Management API

### Discover Devices
**Endpoint**: `POST /api/discover-devices/`

Initiates BACnet device discovery on the network.

**Response**:
```json
{
  "success": true,
  "message": "Device discovery completed with 3 devices"
}
```

### Read Device Points
**Endpoint**: `POST /api/devices/{device_id}/read-points/`

Reads current values from all points on a specific device.

**Response**:
```json
{
  "success": true,
  "message": "Read 45 sensor values from device 2000",
  "readings_collected": 45
}
```

### Discover Device Points
**Endpoint**: `POST /api/devices/{device_id}/discover-points/`

Discovers and catalogs all available points on a specific device.

**Response**:
```json
{
  "success": true,
  "message": "Discovered 45 points for device 2000",
  "device_id": 2000,
  "estimated_time": "5-10 seconds",
  "status": "reading"
}
```

### Get Device Values
**Endpoint**: `GET /api/devices/{device_id}/values/`

Returns current values for all points on a specific device.

**Response**:
```json
{
  "success": true,
  "device_id": 2000,
  "points": [
    {
      "id": 123,
      "identifier": "analogInput:100",
      "object_type": "analogInput",
      "instance_number": 100,
      "object_name": "Temperature Sensor",
      "present_value": "23.5",
      "units": "degreesCelsius",
      "display_value": "23.5 °C",
      "value_last_read": "2024-10-06T15:30:00Z",
      "is_readable": true,
      "data_type": "real"
    }
  ],
  "total_points": 45,
  "readable_points": 40,
  "last_updated": "2024-10-06T15:35:00Z"
}
```

### Clear Devices
**Endpoint**: `POST /api/clear-devices/`

Deactivates all devices and their associated data.

**Response**:
```json
{
  "success": true,
  "message": "Cleared 3 devices and 135 points"
}
```

## Error Handling

All API endpoints return standard error responses:

```json
{
  "success": false,
  "message": "Device 999 not found",
  "error_type": "DeviceNotFoundError"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (validation error)
- `404`: Not Found (device/point not found)
- `429`: Too Many Requests (rate limited)
- `500`: Internal Server Error

## Rate Limiting

API endpoints are rate limited:
- Device Status: 200 requests per hour
- Device Trends: 100 requests per hour
- Management operations: No limit

## Authentication

Currently, all API endpoints allow anonymous access for development purposes.

## Example Usage

### Python (requests)
```python
import requests

# Get device status
response = requests.get('http://127.0.0.1:8000/api/devices/status/')
data = response.json()

# Discover devices
response = requests.post('http://127.0.0.1:8000/api/discover-devices/')
result = response.json()

# Read device points
response = requests.post('http://127.0.0.1:8000/api/devices/2000/read-points/')
readings = response.json()
```

### JavaScript (fetch)
```javascript
// Get device status
fetch('/api/devices/status/')
  .then(response => response.json())
  .then(data => console.log(data));

// Discover devices
fetch('/api/discover-devices/', {method: 'POST'})
  .then(response => response.json())
  .then(result => console.log(result));
```

### curl
```bash
# Get device status
curl http://127.0.0.1:8000/api/devices/status/

# Discover devices
curl -X POST http://127.0.0.1:8000/api/discover-devices/

# Read device points
curl -X POST http://127.0.0.1:8000/api/devices/2000/read-points/

# Get device trends for last 24 hours
curl "http://127.0.0.1:8000/api/devices/2000/trends/?period=24hours"
```

## OpenAPI Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://127.0.0.1:8000/api/docs/
- **ReDoc**: http://127.0.0.1:8000/api/redoc/
- **OpenAPI Schema**: http://127.0.0.1:8000/api/schema/

## Support

For API support and questions, refer to the main project documentation.