from datetime import timedelta

import numpy as np
from django.utils import timezone

from .models import BACnetPoint, BACnetReading


class AnomalyDetector:
    def __init__(self, z_score_threshold=2.5):
        self.z_score_threshold = z_score_threshold

    def detect_z_score_anomaly(self, point: BACnetPoint, new_value: float) -> float:
        numeric_values = []
        point_readings = (
            BACnetReading.objects.filter(
                point=point, read_time__gte=timezone.now() - timedelta(hours=24)
            )
            .exclude(value="0.0")
            .values_list("value", flat=True)
        )

        for value in point_readings:
            try:
                numeric_values.append(float(value))
            except (ValueError, TypeError):
                continue

        mean = np.mean(numeric_values)
        std_dev = np.std(numeric_values)

        if len(numeric_values) < 5 or std_dev == 0:
            return 0.0

        z_score = np.abs(new_value - mean) / std_dev
        return z_score

    def detect_iqr_anomaly(
        self, point: BACnetPoint, new_value: float
    ) -> tuple[float, bool]:
        """
        Detect anomalies using Interquartile Range (IQR) method.
        Returns (iqr_score, is_anomaly) where iqr_score is how many IQRs
        away from median.
        """
        numeric_values = []
        point_readings = (
            BACnetReading.objects.filter(
                point=point, read_time__gte=timezone.now() - timedelta(hours=24)
            )
            .exclude(value="0.0")
            .values_list("value", flat=True)
        )

        for value in point_readings:
            try:
                numeric_values.append(float(value))
            except (ValueError, TypeError):
                continue

        if len(numeric_values) < 5:
            return 0.0, False

        q1 = np.percentile(numeric_values, 25)
        q3 = np.percentile(numeric_values, 75)
        iqr = q3 - q1

        # print(f"DEBUG: IQR method - data points: {len(numeric_values)}")
        # if len(numeric_values) >= 5:
        #     print(f"DEBUG: Q1={q1:.2f}, Q3={q3:.2f}, IQR={iqr:.2f}")

        if iqr == 0:
            return 0.0, False

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        median = np.median(numeric_values)
        iqr_score = np.abs(new_value - median) / iqr

        is_anomaly = (
            True if new_value < lower_bound or new_value > upper_bound else False
        )
        return iqr_score, is_anomaly
