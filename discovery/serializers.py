from rest_framework import serializers


class DeviceStatusSerializer(serializers.Serializer):
    device_id = serializers.IntegerField()
    address = serializers.CharField()
    statistics = serializers.DictField()


class DeviceStatusResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    summary = serializers.DictField()
    devices = DeviceStatusSerializer(many=True)
    timestamp = serializers.DateTimeField()


class TrendsStatisticsSerializer(serializers.Serializer):
    min = serializers.FloatField(allow_null=True)
    max = serializers.FloatField(allow_null=True)
    avg = serializers.FloatField(allow_null=True)
    count = serializers.IntegerField()


class TrendsReadingSerializer(serializers.Serializer):
    timestamp = serializers.DateTimeField()
    value = serializers.FloatField(allow_null=True)


class TrendsPointSerializer(serializers.Serializer):
    point_identifier = serializers.CharField()
    readings = TrendsReadingSerializer(many=True)
    statistics = TrendsStatisticsSerializer()


class DeviceTrendsResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    device_id = serializers.IntegerField()
    period = serializers.CharField()
    points = TrendsPointSerializer(many=True)


class DevicePerformanceSerializer(serializers.Serializer):
    device_id = serializers.IntegerField()
    address = serializers.CharField()
    total_readings = serializers.IntegerField()
    readings_last_24h = serializers.IntegerField()
    avg_data_quality = serializers.FloatField(allow_null=True)
    most_active_point = serializers.CharField(allow_null=True)
    last_reading_time = serializers.DateTimeField(allow_null=True)
    uptime_percentage = serializers.FloatField()


class DevicePerformanceResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    summary = serializers.DictField()
    devices = DevicePerformanceSerializer(many=True)
    timestamp = serializers.DateTimeField()


class DataQualityMetricsSerializer(serializers.Serializer):
    completeness_score = serializers.FloatField()
    accuracy_score = serializers.FloatField()
    freshness_score = serializers.FloatField()
    consistency_score = serializers.FloatField()
    overall_quality_score = serializers.FloatField()


class PointQualitySerializer(serializers.Serializer):
    point_identifier = serializers.CharField()
    total_readings = serializers.IntegerField()
    missing_readings = serializers.IntegerField()
    outlier_count = serializers.IntegerField()
    last_reading_time = serializers.DateTimeField(allow_null=True)
    data_gaps_hours = serializers.FloatField()
    quality_score = serializers.FloatField()


class DeviceDataQualitySerializer(serializers.Serializer):
    device_id = serializers.IntegerField()
    address = serializers.CharField()
    metrics = DataQualityMetricsSerializer()
    point_quality = PointQualitySerializer(many=True)
    data_coverage_percentage = serializers.FloatField()
    avg_reading_interval_minutes = serializers.FloatField(allow_null=True)


class DataQualityResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    summary = DataQualityMetricsSerializer()
    devices = DeviceDataQualitySerializer(many=True)
    timestamp = serializers.DateTimeField()
