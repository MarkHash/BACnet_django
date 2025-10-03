# Energy Analytics System

The BACnet Django application includes a comprehensive energy analytics system that analyzes HVAC energy consumption, efficiency, and provides ML-based forecasting.

## Overview

The energy analytics pipeline processes temperature sensor data to estimate HVAC energy consumption, calculate efficiency scores, and provide next-day forecasting using machine learning algorithms.

## Key Features

- **HVAC Load Estimation**: Temperature deviation-based energy consumption calculations
- **Efficiency Scoring**: Multi-factor scoring system analyzing stability, comfort, and timing
- **ML Forecasting**: Linear regression forecasting for next-day energy consumption
- **Interactive Dashboard**: Real-time metrics with Chart.js visualizations
- **Data Pipeline**: Automated daily metrics calculation with database persistence

## Architecture

### Core Components

1. **EnergyAnalyticsService** (`discovery/energy_analytics.py`)
   - Processes temperature data and calculates energy metrics
   - Implements HVAC load estimation algorithms
   - Provides ML forecasting capabilities

2. **Energy Dashboard** (`/energy-dashboard/`)
   - Interactive web interface with real-time metrics
   - Chart.js integration for energy consumption trends
   - Responsive design with gradient metric cards

3. **Energy Metrics Model** (`discovery/models.py`)
   - Database table storing daily energy analytics
   - Includes temperature statistics, efficiency scores, and forecasts

4. **API Endpoint** (`/api/energy-dashboard/`)
   - RESTful API providing JSON data for frontend consumption
   - Real-time energy analytics with comprehensive device metrics

## Energy Calculations

### HVAC Load Estimation

The system estimates HVAC energy consumption based on temperature deviation from the comfort zone (22°C):

```python
# Formula: (0.5 kWh base + 0.3 kWh/°C * deviation) * data_coverage_ratio
estimated_load = BASE_HVAC_LOAD_KWH * data_coverage_ratio + (
    LOAD_PER_DEGREE_KWH * temp_deviation * data_coverage_ratio
)
```

**Parameters**:
- `BASE_HVAC_LOAD_KWH`: 0.5 kWh (baseline consumption)
- `LOAD_PER_DEGREE_KWH`: 0.3 kWh per degree deviation
- `data_coverage_ratio`: Scales energy based on actual readings collected
- `temp_deviation`: Average absolute deviation from 22°C comfort zone

### Efficiency Scoring

HVAC efficiency is calculated using a multi-factor scoring system (0-100):

```python
# Scoring: Stability (40pts) + Comfort (40pts) + Timing (20pts)
efficiency_score = stability_score + comfort_score + timing_score
```

**Components**:
1. **Stability Score (40 points)**: Based on temperature variance
   - Lower variance = higher stability score
   - Formula: `max(0, 40 - (variance * 10))`

2. **Comfort Score (40 points)**: Based on deviation from 22°C
   - Closer to 22°C = higher comfort score
   - Formula: `max(0, 40 - (temp_deviation * 5))`

3. **Timing Score (20 points)**: Based on peak demand timing
   - Night hours (22:00-06:00): 20 points (off-peak efficient)
   - Day hours (07:00-11:00, 19:00-21:00): 10 points
   - Peak hours (12:00-18:00): 5 points

### ML Forecasting

The system uses linear regression to predict next-day energy consumption:

```python
# Features: [hour, temperature_deviation]
# Target: temperature_deviation (proxy for energy load)
model = LinearRegression()
model.fit(X, y)

# Forecast next 24 hours
forecast = model.predict(next_day_features)
daily_forecast = forecast.mean()
confidence = min(len(data_points) / 100, 0.95)
```

**Features**:
- **Hour of day**: Captures daily energy patterns
- **Temperature deviation**: Primary driver of HVAC load
- **Confidence scoring**: Based on available data points (more data = higher confidence)

## Data Processing Pipeline

### Daily Metrics Calculation

The `calculate_daily_metrics()` method processes all devices daily:

1. **Temperature Data Extraction**
   - Filters readings by units containing "degree"
   - Excludes non-numeric and invalid values
   - Groups readings by device and date

2. **Statistical Analysis**
   - Calculates temperature statistics (min, max, avg, variance)
   - Identifies peak demand hours
   - Processes data coverage ratios

3. **Energy Estimation**
   - Computes HVAC load based on temperature deviation
   - Calculates efficiency scores using multi-factor system
   - Generates ML forecasts with confidence intervals

4. **Database Persistence**
   - Creates/updates EnergyMetrics records
   - Stores daily analytics for historical tracking
   - Enables trend analysis and reporting

### Data Requirements

**Minimum Requirements**:
- 5+ temperature readings per device per day
- Temperature units containing "degree" (°C, °F)
- Valid numeric temperature values

**Optimal Performance**:
- 288 readings per day (5-minute intervals)
- Consistent reading intervals
- Multiple temperature sensors per building

## Dashboard Interface

### Energy Metrics Cards

The dashboard displays key metrics in responsive cards:

1. **Total Energy Consumed** (kWh)
   - Sum of estimated HVAC loads across all devices
   - Color-coded based on consumption levels

2. **Average Efficiency Score** (0-100)
   - Mean efficiency score across all devices
   - Color-coded: Green (80+), Yellow (60-79), Red (<60)

3. **Devices with Energy Data**
   - Count of devices with sufficient temperature data
   - Percentage of total active devices

4. **Peak Demand Time**
   - Hour of highest energy consumption
   - Based on temperature deviation analysis

### Energy Trends Chart

Interactive Chart.js visualization showing:
- **Hourly energy consumption** (24-hour view)
- **Temperature trends** with efficiency overlays
- **Forecast predictions** with confidence bands
- **Historical comparisons** for trend analysis

### Device-Specific Analytics

Each device card displays:
- **Current efficiency score** with color-coded badge
- **Temperature statistics** (min, max, avg, variance)
- **Estimated energy consumption** for the current day
- **ML forecast** for next-day consumption with confidence
- **Peak demand hour** and timing efficiency

## API Integration

### Energy Dashboard API

**Endpoint**: `GET /api/energy-dashboard/`

**Response Structure**:
```json
{
  "success": true,
  "data": {
    "total_devices": 6,
    "devices_with_energy_data": 4,
    "total_energy_consumed": 127.45,
    "average_efficiency_score": 78.5,
    "devices": [...],
    "trends": [...]
  }
}
```

### Real-Time Updates

The dashboard automatically refreshes data every 30 seconds using JavaScript:
```javascript
// Auto-refresh energy data
setInterval(loadEnergyData, 30000);
```

## Configuration

### Energy Constants

Key configuration parameters in `discovery/constants.py`:

```python
# Energy calculation constants
BASE_HVAC_LOAD_KWH = 0.5          # Base HVAC consumption
LOAD_PER_DEGREE_KWH = 0.3         # Energy per degree deviation
READINGS_PER_DAY = 288             # Expected readings (5-min intervals)
COMFORT_ZONE_CENTER = 22.0         # Optimal temperature (°C)
```

### Efficiency Scoring Weights

```python
# Efficiency score components
STABILITY_WEIGHT = 0.4             # Temperature variance impact
COMFORT_WEIGHT = 0.4               # Comfort zone adherence
TIMING_WEIGHT = 0.2                # Peak demand timing
```

## Implementation Examples

### Manual Metrics Calculation

```python
from discovery.energy_analytics import EnergyAnalyticsService
from datetime import date

# Initialize service
service = EnergyAnalyticsService()

# Calculate metrics for today
metrics_created = service.calculate_daily_metrics(date.today())
print(f"Created metrics for {metrics_created} devices")
```

### Custom Energy Analysis

```python
from discovery.models import EnergyMetrics, BACnetDevice

# Get energy metrics for specific device
device = BACnetDevice.objects.get(device_id=2000)
metrics = EnergyMetrics.objects.filter(device=device).latest('date')

print(f"Efficiency Score: {metrics.efficiency_score}")
print(f"Estimated Load: {metrics.estimated_hvac_load} kWh")
print(f"Forecast: {metrics.predicted_next_day_load} kWh")
```

### Temperature Data Query

```python
from discovery.models import BACnetReading
from django.utils import timezone
from datetime import timedelta

# Get recent temperature readings
temp_readings = BACnetReading.objects.filter(
    point__units__icontains='degree',
    read_time__gte=timezone.now() - timedelta(hours=24)
).exclude(
    value='0.0'  # Exclude invalid readings
)
```

## Performance Optimization

### Database Queries

The system uses optimized queries:
- **Bulk operations**: ProcessManager for batch database updates
- **Efficient filtering**: Indexed queries on timestamp and device fields
- **Selective processing**: Only processes devices with temperature sensors

### Caching Strategy

- **Dashboard data**: 5-minute cache for energy metrics
- **Historical trends**: 1-hour cache for chart data
- **Device statistics**: Real-time updates for current values

### Memory Management

- **Streaming processing**: Processes devices sequentially to manage memory
- **Data cleanup**: Automatic removal of old readings beyond retention period
- **Efficient serialization**: Optimized JSON responses for API endpoints

## Troubleshooting

### Common Issues

1. **No Energy Data Available**
   - Verify temperature sensors are present and readable
   - Check that units contain "degree" in the point configuration
   - Ensure sufficient readings (5+ per day minimum)

2. **Low Efficiency Scores**
   - High temperature variance indicates HVAC instability
   - Large deviations from 22°C comfort zone reduce scores
   - Peak demand during expensive hours (12:00-18:00) impacts timing score

3. **ML Forecast Issues**
   - Insufficient historical data (need 5+ readings)
   - Non-numeric temperature values in dataset
   - Extreme outliers affecting model training

### Debug Commands

```python
# Check temperature sensor availability
from discovery.models import BACnetPoint
temp_sensors = BACnetPoint.objects.filter(units__icontains='degree')
print(f"Temperature sensors found: {temp_sensors.count()}")

# Verify recent readings
from discovery.models import BACnetReading
recent_readings = BACnetReading.objects.filter(
    point__in=temp_sensors,
    read_time__gte=timezone.now() - timedelta(hours=24)
).count()
print(f"Recent temperature readings: {recent_readings}")

# Test energy calculation
from discovery.energy_analytics import EnergyAnalyticsService
service = EnergyAnalyticsService()
metrics_created = service.calculate_daily_metrics()
print(f"Metrics created: {metrics_created}")
```

## Future Enhancements

### Planned Features

1. **Advanced ML Models**
   - LSTM neural networks for seasonal forecasting
   - Multi-variate analysis including weather data
   - Anomaly detection integration for efficiency alerts

2. **Cost Analysis**
   - Time-of-use electricity pricing integration
   - Cost optimization recommendations
   - ROI analysis for HVAC improvements

3. **Building-Level Analytics**
   - Multi-device aggregation and correlation
   - Zone-based efficiency analysis
   - Comparative benchmarking across buildings

4. **Real-Time Optimization**
   - Predictive control recommendations
   - Automated efficiency alerts
   - Integration with building management systems

### Contributing

To extend the energy analytics system:

1. **Add new metrics**: Extend the `EnergyMetrics` model
2. **Implement algorithms**: Add methods to `EnergyAnalyticsService`
3. **Create visualizations**: Extend the dashboard with new Chart.js components
4. **Optimize performance**: Profile and optimize database queries
5. **Add tests**: Create unit tests for new calculation methods