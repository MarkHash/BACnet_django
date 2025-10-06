from datetime import timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
from django.utils import timezone
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

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

        self.ISOLATION_CONTAMINATION = 0.1
        self.MIN_ISOLATION_SAMPLES = 20

        self.ENSEMBLE_WEIGHTS = {"z_score": 0.4, "iqr": 0.3, "isolation_forest": 0.3}

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
            if len(values) < self.MIN_DATA_POINTS:
                raise InsufficientAnomalyDataError(
                    point.id, len(values), self.MIN_DATA_POINTS
                )

            mean = np.mean(values)
            std_dev = np.std(values)

            if std_dev == 0:
                raise InsufficientAnomalyDataError(
                    point.id, len(values), self.MIN_DATA_POINTS
                )

            z_score = np.abs(new_value - mean) / std_dev
            return z_score
        except (ValueError, TypeError, np.linalg.LinAlgError) as e:
            raise StatisticalCalculationError(
                point.id, "z_score", f"Numpy calculation failed: {e}"
            )

    def _calculate_iqr_bounds(
        self, point: BACnetPoint, values: list[float]
    ) -> tuple[float, float, float, float]:
        """Calculate IQR bounds and median."""
        if len(values) < self.MIN_DATA_POINTS:
            raise InsufficientAnomalyDataError(
                point.id, len(values), self.MIN_DATA_POINTS
            )

        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1

        if iqr == 0:
            raise StatisticalCalculationError(
                point.id, "iqr", "IQR is zero - no variance in data"
            )

        lower_bound = q1 - self.IQR_MULTIPLIER * iqr
        upper_bound = q3 + self.IQR_MULTIPLIER * iqr
        median = np.median(values)

        return lower_bound, upper_bound, median, iqr

    def _get_recent_readings_with_timestamps(
        self, point: BACnetPoint, hours_back: int = 24
    ) -> List[Tuple[float, int]]:
        """Get recent readings with hour-of-day for feature engineering."""
        try:
            readings_data = []
            point_readings = (
                BACnetReading.objects.filter(
                    point=point,
                    read_time__gte=timezone.now() - timedelta(hours=hours_back),
                )
                .exclude(value="0.0")
                .values_list("value", "read_time")
            )

            for value_str, read_time in point_readings:
                try:
                    value = float(value_str)
                    hour_of_day = read_time.hour
                    readings_data.append((value, hour_of_day))
                except (ValueError, TypeError):
                    continue
            return readings_data
        except Exception as e:
            raise AnomalyDetectionError(
                point.id, f"Failed to fetch timestamped data: {e}"
            )

    def _create_feature_matrix(
        self, readings_data: List[Tuple[float, int]], new_value: float
    ) -> Optional[np.ndarray]:
        """
        Create feature matrix for Isolation Forest.
        Features: [temperature_value, hour_of_day, rate_of_change]
        """
        try:
            if len(readings_data) < 2:
                return None
            features = []

            for i, (value, hour) in enumerate(readings_data):
                if i > 0:
                    rate_of_change = value - readings_data[i - 1][0]
                else:
                    rate_of_change = 0.0
                features.append([value, hour, rate_of_change])

            if len(readings_data) > 0:
                last_value = readings_data[-1][0]
                new_hour = timezone.now().hour
                new_rate_of_change = new_value - last_value
                features.append([new_value, new_hour, new_rate_of_change])

            return np.array(features)
        except Exception as e:
            print(f"Warning: Feature matrix creation failed: {e}")
            return None

    def _train_isolation_forest(self, features: np.ndarray) -> Tuple[float, bool]:
        """
        Train Isolation Forest and predict anomaly for the last sample.
        Returns (isolation_score, is_anomaly)
        """
        try:
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)

            iso_forest = IsolationForest(
                contamination=self.ISOLATION_CONTAMINATION,
                random_state=42,
                n_estimators=100,
            )

            iso_forest.fit(features_scaled)

            new_sample = features_scaled[-1:]
            anomaly_score = iso_forest.decision_function(new_sample)[0]
            prediction = iso_forest.predict(new_sample)[0]

            is_anomaly = prediction == -1

            return anomaly_score, is_anomaly

        except Exception as e:
            print(f"Warning: Isolation Forest training failed: {e}")
            return 0.0, False

    def detect_isolation_forest_anomaly(
        self, point: BACnetPoint, new_value: float
    ) -> Tuple[float, bool]:
        """
        Detect anomalies using Isolation Forest method.
        Returns (isolation_score, is_anomaly) where isolation_score is anomaly score.
        """
        try:
            recent_readings = self._get_recent_readings_with_timestamps(
                point, self.LOOKBACK_HOURS
            )

            if len(recent_readings) < self.MIN_ISOLATION_SAMPLES:
                return 0.0, False

            features = self._create_feature_matrix(recent_readings, new_value)
            if features is None or len(features) < self.MIN_ISOLATION_SAMPLES:
                return 0.0, False

            isolation_score, is_anomaly = self._train_isolation_forest(features)

            return isolation_score, is_anomaly

        except Exception as e:
            print(f"Warning: Isolation Forest detection failed: {e}")
            return 0.0, False

    def detect_ensemble_anomaly(
        self, point: BACnetPoint, new_value: float
    ) -> Tuple[float, bool, Dict[str, float]]:
        """
        Ensemble anomaly detection combining Z-score, IQR, and Isolation Forest.
        Returns (confidence_score, is_anomaly, method_contributions)
        """
        try:
            z_score = self.detect_z_score_anomaly(point, new_value)
            iqr_score, iqr_anomaly = self.detect_iqr_anomaly(point, new_value)
            iso_score, iso_anomaly = self.detect_isolation_forest_anomaly(
                point, new_value
            )

            z_score_norm = min(z_score / self.z_score_threshold, 1.0)
            iqr_score_norm = min(iqr_score / 2.0, 1.0)
            iso_score_norm = abs(iso_score)

            ensemble_score = (
                self.ENSEMBLE_WEIGHTS["z_score"] * z_score_norm
                + self.ENSEMBLE_WEIGHTS["iqr"] * iqr_score_norm
                + self.ENSEMBLE_WEIGHTS["isolation_forest"] * iso_score_norm
            )

            z_anomaly = z_score >= self.z_score_threshold
            is_anomaly = z_anomaly or iqr_anomaly or iso_anomaly or ensemble_score > 0.6

            method_contributions = {
                "z_score": z_score_norm,
                "iqr": iqr_score_norm,
                "isolation_forest": iso_score_norm,
                "ensemble": ensemble_score,
            }
            return ensemble_score, is_anomaly, method_contributions

        except Exception as e:
            print(f"Warning: Ensemble detection failed: {e}")
            z_score = self.detect_z_score_anomaly(point, new_value)
            is_anomaly = z_score >= self.z_score_threshold
            return z_score / self.z_score_threshold, is_anomaly, {"z_score": 1.0}
