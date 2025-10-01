import numpy as np
import pandas as pd
from django.db.models import Max, Min
from django.utils import timezone
from sklearn.linear_model import LinearRegression

from .models import BACnetDevice, BACnetReading, EnergyMetrics


class EnergyAnalyticsService:
    def __init__(self):
        self.energy_cost_per_kwh = 0.12
        self.comfort_zone_center = 22.0
        self.hvac_efficiency_baseline = 2.5

    def calculate_daily_metrics(self, date=None):
        """Calculate energy metrics for all devices on a given date"""
        if date is None:
            date = timezone.now().date()

        devices = BACnetDevice.objects.all()
        metrics_created = 0

        for device in devices:
            # Check temperature readings specifically
            temp_readings = BACnetReading.objects.filter(
                point__units__icontains="degree"
            )
            date_range = temp_readings.aggregate(
                earliest=Min("read_time"), latest=Max("read_time")
            )
            print(f"Earliest: {date_range['earliest']}")
            print(f"Latest: {date_range['latest']}")

            readings = BACnetReading.objects.filter(
                point__device=device,
                read_time__date=date,
                point__units__icontains="degree",
            ).values_list("value", "read_time")

            print(f"Readings: {readings}")

            if not readings:
                continue

            df = pd.DataFrame(readings, columns=["temperature", "timestamp"])
            df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")
            df = df.dropna()

            if len(df) < 5:
                continue

            temp_stats = {
                "avg_temperature": df["temperature"].mean(),
                "min_temperature": df["temperature"].min(),
                "max_temperature": df["temperature"].max(),
                "temperature_variance": df["temperature"].var(),
            }

            comfort_zone_center = self.comfort_zone_center
            abs(df["temperature"] - comfort_zone_center).mean()
            # estimated_load = self._calculate_hvac_load(temp_deviation, len(df))
            estimated_load = 1.5  # TODO: implement _calculate_hvac_load()
            df["hour"] = df["timestamp"].dt.hour
            hourly_demand = df.groupby("hour")["temperature"].apply(
                lambda x: abs(x - comfort_zone_center).mean()
            )
            peak_hour = hourly_demand.idxmax() if not hourly_demand.empty else None

            efficiency_score = 75.0  # TODO implemente _calculate_efficiency_score()
            # next_day_load = 1.8 # TODO implement _forecast_next_day_load()

            df["temp_deviation"] = abs(df["temperature"] - comfort_zone_center)
            X = df[["hour", "temp_deviation"]].values
            y = df["temp_deviation"].values

            model = LinearRegression()
            model.fit(X, y)

            next_day_hours = np.arange(24).reshape(-1, 1)
            avg_temp_dev = df["temp_deviation"].mean()
            next_day_features = np.column_stack(
                [next_day_hours.flatten(), np.full(24, avg_temp_dev)]
            )

            forecast = model.predict(next_day_features)
            daily_forecast = forecast.mean()
            confidence = min(len(df) / 100, 0.95)

            EnergyMetrics.objects.update_or_create(
                date=date,
                device=device,
                defaults={
                    **temp_stats,
                    "estimated_hvac_load": estimated_load,
                    "peak_demand_hour": peak_hour,
                    "efficiency_score": efficiency_score,
                    "predicted_next_day_load": daily_forecast,
                    "confidence_score": confidence,
                },
            )
            metrics_created += 1

        return metrics_created

    def generate_building_forecast(self, days_ahead=1):
        """Generate 24-hour energy forecast for the building"""

    def get_energy_insights(self, days_back=7):
        """Get comprehensive energy insights for dashboard"""
