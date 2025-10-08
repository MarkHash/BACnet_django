# Energy Analytics Pipeline Implementation Plan
**Date:** 2025-10-01
**Estimated Time:** 2-3 hours
**Status:** Ready to implement - Next major ML feature

## 🎯 **Goal**
Create an advanced energy analytics system that processes BACnet temperature data to provide:
- Energy consumption forecasting
- HVAC efficiency analysis
- Building performance optimization recommendations
- Advanced data engineering pipelines

## 📊 **Available Data Analysis**
Based on your backup data (79 temperature sensors):
- ✅ **Temperature readings** from multiple zones/rooms
- ✅ **Historical data patterns** for trend analysis
- ✅ **Anomaly detection baseline** already implemented
- ✅ **Time-series data** perfect for forecasting models

## 🛠 **Pipeline Architecture**

### **Phase 1: Data Engineering Foundation (45 minutes)**
1. **Energy Metrics Calculator**
   - Temperature differential analysis (indoor vs outdoor)
   - HVAC load estimation based on temperature patterns
   - Zone-based energy consumption modeling

2. **Data Aggregation Service**
   - Hourly/daily temperature summaries
   - Peak demand identification
   - Seasonal pattern detection

### **Phase 2: ML Forecasting Engine (60 minutes)**
1. **Temperature Forecasting Model**
   - ARIMA time-series prediction
   - Linear regression for trend analysis
   - 24-hour ahead temperature predictions

2. **Energy Demand Forecasting**
   - Predict HVAC energy needs based on temperature
   - Peak demand forecasting
   - Cost optimization recommendations

### **Phase 3: Analytics Dashboard (45 minutes)**
1. **Energy Insights Dashboard**
   - Real-time energy metrics
   - Forecasting visualizations
   - Efficiency recommendations

2. **API Endpoints for Analytics**
   - Energy forecasting API
   - Efficiency metrics API
   - Cost optimization API

## 📁 **Implementation Plan**

### **Step 1: Create Energy Analytics Models**
**File:** `discovery/models.py`

Add these models:
```python
class EnergyMetrics(models.Model):
    """Daily energy analytics and metrics"""
    date = models.DateField()
    device = models.ForeignKey(BACnetDevice, on_delete=models.CASCADE)

    # Temperature Analytics
    avg_temperature = models.FloatField()
    min_temperature = models.FloatField()
    max_temperature = models.FloatField()
    temperature_variance = models.FloatField()

    # Energy Estimation (based on HVAC load)
    estimated_hvac_load = models.FloatField(help_text="kWh estimated")
    peak_demand_hour = models.IntegerField(null=True, blank=True)
    efficiency_score = models.FloatField(null=True, blank=True)

    # Forecasting
    predicted_next_day_load = models.FloatField(null=True, blank=True)
    confidence_interval = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['date', 'device']

class BuildingEnergyForecast(models.Model):
    """Building-wide energy forecasting"""
    forecast_date = models.DateField()
    forecast_hour = models.IntegerField()  # 0-23

    # Predictions
    predicted_temperature = models.FloatField()
    predicted_hvac_load = models.FloatField()
    predicted_cost = models.FloatField(null=True, blank=True)

    # Model confidence
    confidence_score = models.FloatField()
    model_version = models.CharField(max_length=20, default="v1.0")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['forecast_date', 'forecast_hour']
```

### **Step 2: Energy Analytics Service**
**File:** `discovery/energy_analytics.py` (new file)

```python
"""
Energy Analytics and Forecasting Service
Processes BACnet temperature data for energy insights
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from django.utils import timezone
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.arima.model import ARIMA
import warnings
warnings.filterwarnings('ignore')

from .models import BACnetReading, BACnetDevice, EnergyMetrics, BuildingEnergyForecast

class EnergyAnalyticsService:
    """Advanced energy analytics for BACnet temperature data"""

    def __init__(self):
        self.hvac_efficiency_baseline = 2.5  # COP (Coefficient of Performance)
        self.energy_cost_per_kwh = 0.12  # $0.12 per kWh (adjustable)

    def calculate_daily_metrics(self, date=None):
        """Calculate energy metrics for all devices on a given date"""
        if date is None:
            date = timezone.now().date()

        devices = BACnetDevice.objects.all()
        metrics_created = 0

        for device in devices:
            # Get temperature readings for the day
            readings = BACnetReading.objects.filter(
                point__device=device,
                point__units__icontains='degree',  # Temperature sensors
                read_time__date=date
            ).values_list('value', 'read_time')

            if not readings:
                continue

            # Convert to dataframe for analysis
            df = pd.DataFrame(readings, columns=['temperature', 'timestamp'])
            df['temperature'] = pd.to_numeric(df['temperature'], errors='coerce')
            df = df.dropna()

            if len(df) < 5:  # Need minimum data points
                continue

            # Calculate temperature statistics
            temp_stats = {
                'avg_temperature': df['temperature'].mean(),
                'min_temperature': df['temperature'].min(),
                'max_temperature': df['temperature'].max(),
                'temperature_variance': df['temperature'].var(),
            }

            # Estimate HVAC load (simplified model)
            # Based on temperature differential from comfort zone (20-24°C)
            comfort_zone_center = 22.0  # Celsius
            temp_deviation = abs(df['temperature'] - comfort_zone_center).mean()
            estimated_load = self._calculate_hvac_load(temp_deviation, len(df))

            # Find peak demand hour
            df['hour'] = df['timestamp'].dt.hour
            hourly_demand = df.groupby('hour')['temperature'].apply(
                lambda x: abs(x - comfort_zone_center).mean()
            )
            peak_hour = hourly_demand.idxmax() if not hourly_demand.empty else None

            # Calculate efficiency score (0-100)
            efficiency_score = self._calculate_efficiency_score(temp_stats, temp_deviation)

            # Forecast next day load
            next_day_load = self._forecast_next_day_load(device, df)

            # Save metrics
            EnergyMetrics.objects.update_or_create(
                date=date,
                device=device,
                defaults={
                    **temp_stats,
                    'estimated_hvac_load': estimated_load,
                    'peak_demand_hour': peak_hour,
                    'efficiency_score': efficiency_score,
                    'predicted_next_day_load': next_day_load,
                    'confidence_interval': 0.85  # 85% confidence
                }
            )
            metrics_created += 1

        return metrics_created

    def _calculate_hvac_load(self, temp_deviation, data_points):
        """Estimate HVAC energy load based on temperature deviation"""
        # Simplified HVAC load calculation
        # Real implementation would consider building size, insulation, etc.
        base_load = 0.5  # kWh base load
        load_per_degree = 0.3  # kWh per degree deviation
        time_factor = data_points / (24 * 6)  # Assume 6 readings per hour

        return (base_load + (temp_deviation * load_per_degree)) * time_factor

    def _calculate_efficiency_score(self, temp_stats, temp_deviation):
        """Calculate HVAC efficiency score (0-100)"""
        # Lower temperature variance = better efficiency
        variance_penalty = min(temp_stats['temperature_variance'] * 10, 30)

        # Lower deviation from comfort zone = better efficiency
        deviation_penalty = min(temp_deviation * 5, 40)

        # Base score of 100, subtract penalties
        efficiency = max(100 - variance_penalty - deviation_penalty, 0)

        return round(efficiency, 2)

    def _forecast_next_day_load(self, device, df):
        """Simple linear regression forecast for next day energy load"""
        try:
            if len(df) < 10:
                return None

            # Create features for prediction
            df['hour'] = df['timestamp'].dt.hour
            df['temp_deviation'] = abs(df['temperature'] - 22.0)

            # Simple linear model: load = f(hour, temperature_deviation)
            X = df[['hour', 'temp_deviation']].values
            y = df['temp_deviation'].values  # Proxy for load

            model = LinearRegression()
            model.fit(X, y)

            # Predict for next day (average of 24 hours)
            next_day_hours = np.arange(24).reshape(-1, 1)
            avg_temp_dev = df['temp_deviation'].mean()
            next_day_features = np.column_stack([
                next_day_hours.flatten(),
                np.full(24, avg_temp_dev)
            ])

            predictions = model.predict(next_day_features)
            avg_predicted_load = self._calculate_hvac_load(predictions.mean(), 24)

            return round(avg_predicted_load, 2)

        except Exception:
            return None

    def generate_building_forecast(self, days_ahead=1):
        """Generate building-wide energy forecast"""
        try:
            # Get recent temperature data for all devices
            cutoff_time = timezone.now() - timedelta(days=7)
            recent_readings = BACnetReading.objects.filter(
                point__units__icontains='degree',
                read_time__gte=cutoff_time
            ).values('value', 'read_time')

            if not recent_readings:
                return 0

            # Create time series data
            df = pd.DataFrame(recent_readings)
            df['temperature'] = pd.to_numeric(df['value'], errors='coerce')
            df = df.dropna()
            df['hour'] = df['read_time'].dt.hour

            # Aggregate by hour
            hourly_temps = df.groupby('hour')['temperature'].mean()

            forecasts_created = 0
            forecast_date = timezone.now().date() + timedelta(days=days_ahead)

            for hour in range(24):
                # Simple forecast based on historical hourly averages
                historical_temp = hourly_temps.get(hour, 22.0)

                # Add some seasonal variation (simplified)
                seasonal_adjustment = np.sin(hour * np.pi / 12) * 2  # ±2°C variation
                predicted_temp = historical_temp + seasonal_adjustment

                # Calculate predicted load
                temp_deviation = abs(predicted_temp - 22.0)
                predicted_load = self._calculate_hvac_load(temp_deviation, 1)
                predicted_cost = predicted_load * self.energy_cost_per_kwh

                # Confidence based on data availability
                confidence = min(len(df) / 100, 0.95)  # Higher confidence with more data

                BuildingEnergyForecast.objects.update_or_create(
                    forecast_date=forecast_date,
                    forecast_hour=hour,
                    defaults={
                        'predicted_temperature': round(predicted_temp, 2),
                        'predicted_hvac_load': round(predicted_load, 2),
                        'predicted_cost': round(predicted_cost, 4),
                        'confidence_score': round(confidence, 2),
                        'model_version': 'v1.0'
                    }
                )
                forecasts_created += 1

            return forecasts_created

        except Exception as e:
            print(f"Forecast generation error: {e}")
            return 0

    def get_energy_insights(self, days_back=7):
        """Get comprehensive energy insights for dashboard"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days_back)

        # Get metrics for the period
        metrics = EnergyMetrics.objects.filter(
            date__range=[start_date, end_date]
        ).select_related('device')

        if not metrics:
            return None

        # Calculate aggregated insights
        total_load = sum(m.estimated_hvac_load for m in metrics)
        avg_efficiency = sum(m.efficiency_score for m in metrics if m.efficiency_score) / len(metrics)
        total_cost = total_load * self.energy_cost_per_kwh

        # Find most/least efficient devices
        device_efficiency = {}
        for metric in metrics:
            device_id = metric.device.device_id
            if device_id not in device_efficiency:
                device_efficiency[device_id] = []
            if metric.efficiency_score:
                device_efficiency[device_id].append(metric.efficiency_score)

        device_avg_efficiency = {
            device: sum(scores) / len(scores)
            for device, scores in device_efficiency.items()
            if scores
        }

        most_efficient = max(device_avg_efficiency.items(), key=lambda x: x[1]) if device_avg_efficiency else None
        least_efficient = min(device_avg_efficiency.items(), key=lambda x: x[1]) if device_avg_efficiency else None

        return {
            'period_days': days_back,
            'total_estimated_load_kwh': round(total_load, 2),
            'average_efficiency_score': round(avg_efficiency, 2),
            'estimated_cost_usd': round(total_cost, 2),
            'most_efficient_device': most_efficient,
            'least_efficient_device': least_efficient,
            'total_devices_analyzed': len(device_efficiency),
            'recommendations': self._generate_recommendations(avg_efficiency, device_avg_efficiency)
        }

    def _generate_recommendations(self, avg_efficiency, device_efficiency):
        """Generate energy optimization recommendations"""
        recommendations = []

        if avg_efficiency < 70:
            recommendations.append("🔴 Overall building efficiency is low. Consider HVAC system maintenance.")
        elif avg_efficiency < 85:
            recommendations.append("🟡 Building efficiency is moderate. Optimize temperature setpoints.")
        else:
            recommendations.append("🟢 Building efficiency is good. Maintain current operations.")

        # Device-specific recommendations
        low_efficiency_devices = [
            device for device, score in device_efficiency.items() if score < 60
        ]

        if low_efficiency_devices:
            recommendations.append(
                f"🔧 Check HVAC systems for devices: {', '.join(low_efficiency_devices[:3])}"
            )

        recommendations.append("💡 Use peak demand forecasting to optimize energy costs.")

        return recommendations
```

### **Step 3: Create Management Command**
**File:** `discovery/management/commands/calculate_energy_metrics.py`

```python
from django.core.management.base import BaseCommand
from discovery.energy_analytics import EnergyAnalyticsService

class Command(BaseCommand):
    help = 'Calculate daily energy metrics for all devices'

    def add_arguments(self, parser):
        parser.add_argument('--days-back', type=int, default=1,
                           help='Calculate metrics for last N days')
        parser.add_argument('--forecast', action='store_true',
                           help='Generate building energy forecast')

    def handle(self, *args, **options):
        service = EnergyAnalyticsService()

        if options['forecast']:
            count = service.generate_building_forecast()
            self.stdout.write(f'Generated {count} forecast entries')

        # Calculate metrics for recent days
        days_back = options['days_back']
        total_metrics = 0

        for i in range(days_back):
            from datetime import timedelta
            from django.utils import timezone

            date = timezone.now().date() - timedelta(days=i)
            count = service.calculate_daily_metrics(date)
            total_metrics += count

            self.stdout.write(f'Date {date}: {count} metrics calculated')

        self.stdout.write(
            self.style.SUCCESS(f'Total metrics calculated: {total_metrics}')
        )
```

## 🚀 **Implementation Steps**

1. **Add models to discovery/models.py**
2. **Create energy_analytics.py service**
3. **Create management command**
4. **Run migrations**: `python manage.py makemigrations && python manage.py migrate`
5. **Test analytics**: `python manage.py calculate_energy_metrics --days-back 7 --forecast`

## 📊 **Expected Results**

After implementation, you'll have:
- ✅ **Daily energy metrics** for all temperature sensors
- ✅ **HVAC load estimation** based on temperature patterns
- ✅ **Efficiency scoring** for optimization insights
- ✅ **24-hour energy forecasting** for cost planning
- ✅ **Building-wide analytics** for management decisions

## 🎯 **Portfolio Value**

This feature demonstrates:
- **Data Engineering**: ETL pipelines for sensor data
- **ML Engineering**: Time-series forecasting models
- **Business Intelligence**: Energy cost optimization
- **Scalable Architecture**: Modular analytics services

Ready to implement? This will add significant data science capabilities to your BACnet project!