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
