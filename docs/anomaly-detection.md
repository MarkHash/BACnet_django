# Anomaly Detection System

The BACnet Django application includes a comprehensive real-time anomaly detection system for temperature sensors using statistical analysis methods.

## Overview

The anomaly detection system automatically identifies unusual temperature readings that deviate significantly from normal patterns, helping to detect HVAC malfunctions, sensor failures, or environmental issues.

## Key Features

- **Ensemble Detection**: Z-score + IQR methods working together for robust anomaly detection
- **Temperature Sensor Focus**: Automatically detects and analyzes temperature readings (°C, °F)
- **Real-time Processing**: Anomaly detection runs during data collection
- **Historical Analysis**: Uses 24-hour rolling window for statistical baseline
- **Data Filtering**: Automatic exclusion of invalid readings (0.0°C values)
- **Configurable Thresholds**: Adjustable Z-score threshold (default: 2.5 standard deviations)

## Detection Methods

### Z-Score Detection

Statistical anomaly detection using standard deviation analysis:

```python
z_score = |new_value - mean| / std_deviation
```

**Threshold**: Default 2.5 standard deviations
- **Normal readings**: Z-score < 2.5
- **Anomalous readings**: Z-score ≥ 2.5

### IQR (Interquartile Range) Detection

Outlier detection using quartile ranges, resistant to extreme values:

```python
Q1 = 25th percentile
Q3 = 75th percentile
IQR = Q3 - Q1
lower_bound = Q1 - (1.5 * IQR)
upper_bound = Q3 + (1.5 * IQR)
```

**Anomaly Criteria**: Values outside [lower_bound, upper_bound]

### Ensemble Detection

Combines both methods for robust detection:
- Reading flagged as anomaly if **EITHER** method detects it
- Provides both Z-score and IQR score for analysis
- Reduces false positives while maintaining sensitivity

## Implementation

### Core Components

1. **AnomalyDetector Class** (`discovery/ml_utils.py`)
   ```python
   class AnomalyDetector:
       def __init__(self, z_score_threshold=2.5):
           self.z_score_threshold = z_score_threshold
           self.LOOKBACK_HOURS = 24
           self.MIN_DATA_POINTS = 5
   ```

2. **Temperature Sensor Detection** (`discovery/services.py`)
   ```python
   # Automatically detects temperature sensors by units
   def _is_temperature_sensor(self, point):
       return point.units and 'degree' in point.units.lower()
   ```

3. **Real-time Integration** (`discovery/services.py`)
   ```python
   # Anomaly detection during data collection
   z_score, iqr_score, is_anomaly = self._detect_anomaly_if_temperature(point, value)
   ```

### Database Schema

The `BACnetReading` model includes anomaly detection fields:

```sql
-- Anomaly detection fields
anomaly_score FLOAT NULL,           -- Z-score value
is_anomaly BOOLEAN DEFAULT FALSE    -- Combined anomaly flag
```

## Configuration

### Detection Parameters

```python
# Default configuration in ml_utils.py
Z_SCORE_THRESHOLD = 2.5        # Standard deviations for anomaly detection
LOOKBACK_HOURS = 24            # Historical data window
MIN_DATA_POINTS = 5            # Minimum readings for statistical analysis
IQR_MULTIPLIER = 1.5           # IQR boundary multiplier
```

### Customization

```python
# Custom detector with different threshold
detector = AnomalyDetector(z_score_threshold=3.0)  # More conservative

# Custom lookback period
detector.LOOKBACK_HOURS = 48  # 2-day history
```

## Data Processing

### Temperature Sensor Identification

The system automatically identifies temperature sensors:

```python
# Sensors detected by units containing "degree"
temperature_points = BACnetPoint.objects.filter(
    units__icontains='degree'
)
```

### Data Filtering

Invalid readings are automatically excluded:

```python
# Exclude common invalid values
excluded_values = ['0.0', 'inactive', 'offline', 'error']
```

### Historical Context

Each anomaly detection uses 24-hour rolling history:

```python
# Get recent readings for statistical baseline
recent_readings = BACnetReading.objects.filter(
    point=point,
    read_time__gte=timezone.now() - timedelta(hours=24)
).exclude(value='0.0')
```

## API Endpoints

### List Anomalies
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

### Device-Specific Anomalies
**Endpoint**: `GET /api/v2/anomalies/devices/{device_id}/`

**Example**:
```bash
curl "http://127.0.0.1:8000/api/v2/anomalies/devices/2000/?anomalies_only=true"
```

### Anomaly Statistics
**Endpoint**: `GET /api/v2/anomalies/stats/`

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

## Usage Examples

### Check Recent Anomalies

```python
from discovery.models import BACnetReading
from django.utils import timezone
from datetime import timedelta

# Get anomalous readings from last 24 hours
anomalies = BACnetReading.objects.filter(
    is_anomaly=True,
    read_time__gte=timezone.now() - timedelta(hours=24)
)

for reading in anomalies:
    print(f"Device {reading.point.device.device_id}: "
          f"{reading.value}°C (Z-score: {reading.anomaly_score:.2f})")
```

### Analyze Temperature Patterns

```python
from discovery.models import BACnetPoint

# Get all temperature sensors
temp_sensors = BACnetPoint.objects.filter(units__icontains='degree')

for sensor in temp_sensors:
    recent_anomalies = sensor.readings.filter(
        is_anomaly=True,
        read_time__gte=timezone.now() - timedelta(hours=24)
    ).count()

    print(f"Sensor {sensor.identifier}: {recent_anomalies} anomalies today")
```

### Manual Anomaly Detection

```python
from discovery.ml_utils import AnomalyDetector
from discovery.models import BACnetPoint

detector = AnomalyDetector()
point = BACnetPoint.objects.get(identifier='analogInput:100')

# Test a new temperature reading
new_temperature = 35.0  # °C
z_score = detector.detect_z_score_anomaly(point, new_temperature)
iqr_score, is_iqr_anomaly = detector.detect_iqr_anomaly(point, new_temperature)

print(f"Temperature: {new_temperature}°C")
print(f"Z-score: {z_score:.2f}")
print(f"IQR anomaly: {is_iqr_anomaly}")
```

## Monitoring and Alerting

### Dashboard Integration

The anomaly detection system integrates with the main dashboard:
- **Anomaly count widgets**: Show recent anomaly statistics
- **Device status indicators**: Highlight devices with recent anomalies
- **Historical charts**: Visualize anomaly patterns over time

### Real-time Monitoring

```python
# Monitor anomaly rates in real-time
def get_current_anomaly_rate():
    total_readings = BACnetReading.objects.filter(
        read_time__gte=timezone.now() - timedelta(hours=1)
    ).count()

    anomaly_readings = BACnetReading.objects.filter(
        read_time__gte=timezone.now() - timedelta(hours=1),
        is_anomaly=True
    ).count()

    return (anomaly_readings / total_readings * 100) if total_readings > 0 else 0
```

## Performance Considerations

### Database Optimization

- **Indexed queries**: Anomaly queries use database indexes on `is_anomaly` and `read_time`
- **Efficient lookups**: Statistical calculations use optimized queryset operations
- **Batch processing**: Multiple readings processed together to reduce database calls

### Memory Management

- **Streaming processing**: Temperature data processed in chunks to manage memory
- **Historical limits**: Only uses 24-hour window to prevent excessive memory usage
- **Garbage collection**: Automatic cleanup of intermediate statistical calculations

## Troubleshooting

### Common Issues

1. **No Anomalies Detected**
   - Verify temperature sensors are present: Check `units` field contains "degree"
   - Ensure sufficient data: Need 5+ readings for statistical analysis
   - Check thresholds: Default Z-score threshold is 2.5 (might be too high)

2. **Too Many False Positives**
   - Increase Z-score threshold: Try 3.0 instead of 2.5
   - Check data quality: Remove sensors with unstable readings
   - Verify sensor calibration: Physical sensors may need adjustment

3. **Performance Issues**
   - Monitor database queries: Use Django debug toolbar
   - Optimize lookback period: Reduce from 24 to 12 hours if needed
   - Index optimization: Ensure proper database indexes

### Debug Commands

```python
# Check temperature sensor configuration
from discovery.models import BACnetPoint
temp_sensors = BACnetPoint.objects.filter(units__icontains='degree')
print(f"Temperature sensors: {temp_sensors.count()}")

# Verify recent temperature readings
from discovery.models import BACnetReading
recent_temps = BACnetReading.objects.filter(
    point__units__icontains='degree',
    read_time__gte=timezone.now() - timedelta(hours=24)
).count()
print(f"Recent temperature readings: {recent_temps}")

# Test anomaly detection
from discovery.ml_utils import AnomalyDetector
detector = AnomalyDetector()
# Test with specific point and value
```

## Future Enhancements

### Planned Features

1. **Advanced ML Methods**
   - Isolation Forest for multivariate anomaly detection
   - LSTM neural networks for temporal pattern recognition
   - Seasonal decomposition for long-term trend analysis

2. **Alert System**
   - Email/SMS notifications for critical anomalies
   - Webhook integration for external monitoring systems
   - Escalation policies for persistent anomalies

3. **Visualization Improvements**
   - Interactive anomaly timeline charts
   - Heatmaps showing anomaly patterns across devices
   - Statistical distribution plots for threshold tuning

4. **Performance Optimization**
   - Streaming anomaly detection for real-time processing
   - Distributed processing for large-scale deployments
   - Adaptive thresholds based on historical patterns

### Contributing

To extend the anomaly detection system:

1. **Add new detection methods**: Implement in `ml_utils.py`
2. **Improve visualizations**: Extend dashboard templates
3. **Optimize performance**: Profile and optimize database queries
4. **Add tests**: Create comprehensive test cases for edge conditions
5. **Documentation**: Update this guide with new features