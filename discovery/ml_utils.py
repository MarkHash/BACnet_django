from datetime import timedelta

import numpy as np
from django.utils import timezone

from .models import BACnetPoint, BACnetReading


class AnomalyDetector:
    def __init__(self, z_score_threshold=2.5):
        self.z_score_threshold = z_score_threshold

    def detect_z_score_anomaly(self, point: BACnetPoint, new_value: float) -> float:
        numeric_values = []
        point_readings = BACnetReading.objects.filter(
            point=point, read_time__gte=timezone.now() - timedelta(hours=24)
        ).values_list("value", flat=True)

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
