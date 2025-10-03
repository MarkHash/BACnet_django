from datetime import date, datetime
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from django.db.models import Max, Min
from django.utils import timezone
from sklearn.linear_model import LinearRegression

from .constants import BACnetConstants
from .exceptions import InsufficientDataError, MLForecastError, TemperatureDataError
from .models import BACnetDevice, BACnetReading, EnergyMetrics


class EnergyAnalyticsService:
    def __init__(self):
        self.energy_cost_per_kwh = 0.12
        self.comfort_zone_center = 22.0
        self.hvac_efficiency_baseline = 2.5

    def calculate_daily_metrics(self, date: Optional[date] = None) -> int:
        """
        Process temperature data and calculate energy metrics for all devices.

        Analyzes temperature readings to compute HVAC load, efficiency scores,
        and ML forecasts. Creates/updates EnergyMetrics records for each device.

        Args:
            date: Target date for analysis (defaults to today)

        Returns:
            int: Number of device metrics successfully created
        """
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

            try:
                df = self._get_device_temperature_data(device, date)
                if df is None:
                    continue
                temp_stats = self._calculate_temperature_stats(df, device)
                if temp_stats is None:
                    continue
                temp_deviation = abs(
                    df["temperature"] - self.comfort_zone_center
                ).mean()
                estimated_load = self._calculate_hvac_load(temp_deviation, len(df))
                peak_hour = self._find_peak_demand_hour(df)

                efficiency_score = self._calculate_efficiency_score(
                    temp_stats, temp_deviation, peak_hour
                )
                (daily_forecast, confidence) = self._generate_ml_forecast(df, device)

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

            except InsufficientDataError as e:
                print(f"Skipping device: {str(e)}")
                continue
            except (TemperatureDataError, MLForecastError) as e:
                print(f"Warning: {str(e)}")
                continue

        return metrics_created

    def _get_device_temperature_data(
        self, device: BACnetDevice, date: datetime.date
    ) -> Optional[pd.DataFrame]:
        """Get and clean temperature data for a device on a specific date"""
        try:
            readings = BACnetReading.objects.filter(
                point__device=device,
                read_time__date=date,
                point__units__icontains="degree",
            ).values_list("value", "read_time")

            if not readings:
                return None

            df = pd.DataFrame(readings, columns=["temperature", "timestamp"])
            df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")
            df["hour"] = df["timestamp"].dt.hour
            df = df.dropna()
            return df

        except Exception as e:
            raise TemperatureDataError(device.device_id, f"Data processing failed: {e}")

    def _calculate_temperature_stats(
        self, df: pd.DataFrame, device: BACnetDevice
    ) -> Dict[str, float]:
        """Calculate basic temperature statistics."""
        if len(df) < 5:
            raise InsufficientDataError(device.device_id, len(df))

        return {
            "avg_temperature": df["temperature"].mean(),
            "min_temperature": df["temperature"].min(),
            "max_temperature": df["temperature"].max(),
            "temperature_variance": df["temperature"].var(),
        }

    def _find_peak_demand_hour(self, df: pd.DataFrame) -> Optional[int]:
        """Find hour with highest temperature deviation."""
        comfort_zone_center = self.comfort_zone_center
        hourly_demand = df.groupby("hour")["temperature"].apply(
            lambda x: abs(x - comfort_zone_center).mean()
        )
        return hourly_demand.idxmax() if not hourly_demand.empty else None

    def _generate_ml_forecast(
        self, df: pd.DataFrame, device: BACnetDevice
    ) -> Tuple[Optional[float], float]:
        """Generate ML forecast for next day energy load."""
        try:
            comfort_zone_center = self.comfort_zone_center
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

            return (daily_forecast, confidence)
        except Exception as e:
            raise MLForecastError(device.device_id, e)

    def _calculate_hvac_load(self, temp_deviation: float, reading_count: int) -> float:
        """
        Estimate HVAC energy consumption based on temperature deviation from 22°C.

        Formula: (0.5 kWh base + 0.3 kWh/°C * deviation) * data_coverage_ratio

        The data_coverage_ratio scales energy based on actual readings collected:
        - 1.0 = full day (288 readings), 0.5 = half day, etc.
        - Prevents inflated estimates when data is incomplete

        Args:
            temp_deviation: Average absolute deviation from 22°C comfort zone
            reading_count: Number of temperature readings (max 288 per day)

        Returns:
            float: Estimated HVAC energy in kWh for the measurement period
        """
        data_coverage_ratio = reading_count / BACnetConstants.READINGS_PER_DAY

        estimated_load = BACnetConstants.BASE_HVAC_LOAD_KWH * data_coverage_ratio + (
            BACnetConstants.LOAD_PER_DEGREE_KWH * temp_deviation * data_coverage_ratio
        )
        return estimated_load

    def _calculate_efficiency_score(
        self,
        temp_stats: Dict[str, float],
        temp_deviation: float,
        peak_hour: Optional[int] = None,
    ) -> float:
        """
        Calculate HVAC efficiency score (0-100) based on temperature control.

        Scoring: Stability (40pts) + Comfort (40pts) + Timing (20pts)
        - Lower variance = higher stability score
        - Closer to 22°C = higher comfort score
        - Night peak hours = higher timing score (off-peak efficient)

        Args:
            temp_stats: Dict with 'temperature_variance' key
            temp_deviation: Average deviation from 22°C comfort zone
            peak_hour: Hour (0-23) of peak demand, or None

        Returns:
            float: Efficiency score 0-100
        """
        variance = temp_stats["temperature_variance"]
        stability_score = max(0, 40 - (variance * 10))
        stability_score = min(40, stability_score)

        comfort_score = max(0, 40 - (temp_deviation * 5))
        comfort_score = min(40, comfort_score)

        timing_score = 10
        if peak_hour is not None:
            if 22 <= peak_hour <= 6:  # Night hours
                timing_score = 20
            elif 12 <= peak_hour <= 18:  # peak hours
                timing_score = 5

        total_score = stability_score + comfort_score + timing_score
        return min(100, max(0, total_score))

    def generate_building_forecast(self, days_ahead=1):
        """Generate 24-hour energy forecast for the building"""

    def get_energy_insights(self, days_back=7):
        """Get comprehensive energy insights for dashboard"""
