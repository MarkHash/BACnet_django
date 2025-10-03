from datetime import timedelta

import numpy as np
from django.utils import timezone

from .exceptions import (
    AnomalyDetectionError,
    InsufficientAnomalyDataError,
    StatisticalCalculationError,
)
from .models import BACnetPoint, BACnetReading


class AnomalyDetector:
    def __init__(self, z_score_threshold=2.5):
        self.z_score_threshold = z_score_threshold
        self.LOOKBACK_HOURS = 24
        self.MIN_DATA_POINTS = 5
        self.IQR_MULTIPLIER = 1.5

    def detect_z_score_anomaly(self, point: BACnetPoint, new_value: float) -> float:
        try:
            numeric_values = self._get_recent_numeric_values(point, self.LOOKBACK_HOURS)
            z_score = self._calculate_z_score_stats(point, numeric_values, new_value)
            return z_score
        except InsufficientAnomalyDataError:
            return 0.0
        except StatisticalCalculationError as e:
            print(f"Warning: {str(e)}")
            return 0.0

    def detect_iqr_anomaly(
        self, point: BACnetPoint, new_value: float
    ) -> tuple[float, bool]:
        """
        Detect anomalies using Interquartile Range (IQR) method.
        Returns (iqr_score, is_anomaly) where iqr_score is how many IQRs
        away from median.
        """
        try:
            numeric_values = self._get_recent_numeric_values(point, self.LOOKBACK_HOURS)
            lower_bound, upper_bound, median, iqr = self._calculate_iqr_bounds(
                point, numeric_values
            )
            iqr_score = np.abs(new_value - median) / iqr

            is_anomaly = new_value < lower_bound or new_value > upper_bound
            return iqr_score, is_anomaly
        except InsufficientAnomalyDataError:
            return 0.0, False
        except StatisticalCalculationError as e:
            print(f"Warning: {str(e)}")
            return 0.0, False

    def _get_recent_numeric_values(
        self, point: BACnetPoint, hours_back: int = 24
    ) -> list[float]:
        """Get recent numeric values for a point, excluding invalid data."""
        try:
            numeric_values = []
            point_readings = (
                BACnetReading.objects.filter(
                    point=point,
                    read_time__gte=timezone.now() - timedelta(hours=hours_back),
                )
                .exclude(value="0.0")
                .values_list("value", flat=True)
            )

            for value in point_readings:
                try:
                    numeric_values.append(float(value))
                except (ValueError, TypeError):
                    continue
            return numeric_values
        except Exception as e:
            raise AnomalyDetectionError(point.id, f"Failed to fetch data: {e}")

    def _calculate_z_score_stats(
        self, point: BACnetPoint, values: list[float], new_value: float
    ) -> float:
        """Calculate mean and standard deviation for Z-score method."""
        try:
            mean = np.mean(values)
            std_dev = np.std(values)

            if len(values) < self.MIN_DATA_POINTS or std_dev == 0:
                raise InsufficientAnomalyDataError(
                    point.point_id, len(values), self.MIN_DATA_POINTS
                )

            z_score = np.abs(new_value - mean) / std_dev
            return z_score
        except (ValueError, TypeError, np.linalg.LinAlgError) as e:
            raise StatisticalCalculationError(
                point.point_id, "z_score", f"Numpy calculation failed: {e}"
            )

    def _calculate_iqr_bounds(
        self, point: BACnetPoint, values: list[float]
    ) -> tuple[float, float, float, float]:
        """Calculate IQR bounds and median."""
        if len(values) < self.MIN_DATA_POINTS:
            raise InsufficientAnomalyDataError(
                point.point_id, len(values), self.MIN_DATA_POINTS
            )

        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1

        if iqr == 0:
            raise StatisticalCalculationError(
                point.point_id, "iqr", "IQR is zero - no variance in data"
            )

        lower_bound = q1 - self.IQR_MULTIPLIER * iqr
        upper_bound = q3 + self.IQR_MULTIPLIER * iqr
        median = np.median(values)

        return lower_bound, upper_bound, median, iqr
