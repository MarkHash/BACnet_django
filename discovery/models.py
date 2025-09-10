from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from .constants import BACnetConstants


# Create your models here.
class BACnetDevice(models.Model):
    device_id = models.IntegerField(
        unique=True, help_text="BACnet device instance number"
    )
    address = models.CharField(max_length=50, help_text="IP address of device")
    vendor_id = models.IntegerField(help_text="BACnet vendor ID")

    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now_add=True)

    is_online = models.BooleanField(default=True)
    points_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["device_id"]
        verbose_name = "BACnet Device"
        verbose_name_plural = "BACnet Devices"

    def __str__(self):
        return f"Device {self.device_id} ({self.address})"

    def mark_seen(self):
        self.last_seen = timezone.now()
        self.is_online = True
        self.save()


class BACnetPoint(models.Model):
    device = models.ForeignKey(
        BACnetDevice,
        on_delete=models.CASCADE,
        related_name="points",
        help_text="Device this point belongs to",
    )

    object_type = models.CharField(max_length=50, help_text="BACnet object type")
    instance_number = models.IntegerField(help_text="BACnet instance number")
    identifier = models.CharField(max_length=100, help_text="Full identifier")

    object_name = models.CharField(
        max_length=200, blank=True, help_text="Human-readable name"
    )
    description = models.TextField(blank=True, help_text="Point description")

    present_value = models.CharField(
        max_length=100, blank=True, help_text="Current sensor reading"
    )
    units = models.CharField(
        max_length=50, blank=True, help_text="Engineering units (°F, PSI, etc.)"
    )
    value_last_read = models.DateTimeField(
        null=True, blank=True, help_text="When value was last read"
    )

    DATA_TYPE_CHOICES = [
        ("real", "Real (Float)"),
        ("unsigned", "Unsigned Integer"),
        ("integer", "Signed Integer"),
        ("boolean", "Boolean"),
        ("enumerated", "Enumerated"),
        ("string", "Character String"),
        ("bitstring", "Bit String"),
        ("date", "Date"),
        ("time", "Time"),
        ("datetime", "Date Time"),
        ("null", "Null"),
    ]

    data_type = models.CharField(
        max_length=20,
        choices=DATA_TYPE_CHOICES,
        blank=True,
        help_text="BACnet data type",
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["object_type", "instance_number"]
        unique_together = ["device", "object_type", "instance_number"]
        verbose_name = "BACnet Point"
        verbose_name_plural = "BACnet Points"

    def __str__(self):
        return f"{self.identifier} on {self.device}"

    def update_value(self, value, units=None, data_type=None):
        self.present_value = str(value)
        if units:
            self.units = units
        if data_type:
            self.data_type = data_type
        self.value_last_read = timezone.now()
        self.save()

    def get_display_value(self):
        if not self.present_value:
            return "N/A"

        value = self.present_value

        if isinstance(self.present_value, float):
            value = f"{self.present_value:.2f}"
        elif isinstance(self.present_value, (int, str)) and "." in str(
            self.present_value
        ):
            value = f"{float(self.present_value):.2f}"
        else:
            value = str(value)

        if self.units:
            value = f"{value} {self.units}"
        return value

    @property
    def is_readable(self):
        readable_types = BACnetConstants.READABLE_OBJECT_TYPES

        return self.object_type in readable_types


class BACnetReading(models.Model):
    point = models.ForeignKey(
        BACnetPoint,
        on_delete=models.CASCADE,
        related_name="readings",
        help_text="Point this reading belongs to",
    )

    value = models.CharField(max_length=100, help_text="Sensor reading value")
    units = models.CharField(max_length=50, blank=True, help_text="Engineering units")
    # read_time = models.DateTimeField(
    #     auto_now_add=True, help_text="When reading was taken"
    # )
    read_time = models.DateTimeField(
        default=timezone.now, help_text="When reading was taken"
    )

    quality = models.CharField(
        max_length=50, blank=True, help_text="Reading quality (good, bad, uncertain)"
    )
    priority = models.IntegerField(null=True, blank=True, help_text="Reading priority")
    is_anomaly = models.BooleanField(default=False)
    anomaly_score = models.FloatField(null=True, blank=True)
    data_quality_score = models.FloatField(
        default=1.0, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )

    class Meta:
        ordering = ["-read_time"]
        verbose_name = "BACnet Reading"
        verbose_name_plural = "BACnet Readings"
        indexes = [
            models.Index(fields=["point", "-read_time"]),
        ]

    def __str__(self):
        msg = f"""
        {self.point.identifier}: {self.value} {self.units}
        at {self.read_time.strftime('%H:%M:%S')}
        """
        return msg

    def get_display_value(self):
        if self.units:
            return f"{self.value} {self.units}"
        return self.value


class DeviceStatusHistory(models.Model):
    device = models.ForeignKey(
        BACnetDevice, on_delete=models.CASCADE, related_name="status_history"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    is_online = models.BooleanField()
    response_time_ms = models.FloatField(null=True, blank=True)
    successful_reads = models.IntegerField(default=0)
    failed_reads = models.IntegerField(default=0)
    packet_loss_percent = models.FloatField(
        default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Device Status History"
        verbose_name_plural = "Device Status Histories"
        indexes = [
            models.Index(fields=["device", "-timestamp"]),
        ]

    def __str__(self):
        status = "Online" if self.is_online else "Offline"
        return f"{self.device} - {status} at {self.timestamp}"


class SensorReadingStats(models.Model):
    AGGREGATION_CHOICES = [
        ("hourly", "Hourly"),
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
    ]

    point = models.ForeignKey(
        BACnetPoint, on_delete=models.CASCADE, related_name="statistics"
    )

    aggregation_type = models.CharField(max_length=10, choices=AGGREGATION_CHOICES)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()

    avg_value = models.FloatField(null=True, blank=True)
    min_value = models.FloatField(null=True, blank=True)
    max_value = models.FloatField(null=True, blank=True)
    std_dev = models.FloatField(null=True, blank=True)

    reading_count = models.IntegerField(default=0)
    null_reading_count = models.IntegerField(default=0)
    anomaly_count = models.IntegerField(default=0)

    class Meta:
        ordering = ["-period_start"]
        unique_together = ["point", "aggregation_type", "period_start"]
        verbose_name = "Sensor Reading Statistics"
        verbose_name_plural = "Sensor Reading Statistics"
        indexes = [
            models.Index(fields=["point", "aggregation_type", "-period_start"]),
        ]

    def __str__(self):
        return (
            f"{self.point} - {self.aggregation_type} stats for "
            f"{self.period_start.date()}"
        )


class AlarmHistory(models.Model):
    ALARM_TYPE_CHOICES = [
        ("high_limit", "High Limit Exceeded"),
        ("low_limit", "Low Limit Exceeded"),
        ("communication_failure", "Communication Failure"),
        ("sensor_fault", "Sensor Fault"),
        ("anomaly_detected", "Anomaly Detected"),
        ("maintenance_due", "Maintenance Due"),
    ]

    SEVERITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    device = models.ForeignKey(
        BACnetDevice, on_delete=models.CASCADE, related_name="alarms"
    )

    point = models.ForeignKey(
        BACnetPoint,
        on_delete=models.CASCADE,
        related_name="alarms",
        null=True,
        blank=True,
    )

    alarm_type = models.CharField(max_length=30, choices=ALARM_TYPE_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)

    triggered_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    trigger_value = models.CharField(max_length=100, blank=True)
    threshold_value = models.CharField(max_length=100, blank=True)
    message = models.TextField()

    class Meta:
        ordering = ["-triggered_at"]
        verbose_name = "Alarm History"
        verbose_name_plural = "Alarm Histories"
        indexes = [
            models.Index(fields=["device", "-triggered_at"]),
            models.Index(fields=["is_active", "severity"]),
        ]

    def __str__(self):
        status = "Active" if self.is_active else "Resolved"
        return f"{self.device} - {self.alarm_type} ({status})"

    def resolve(self):
        self.is_active = False
        self.resolved_at = timezone.now()
        self.save()


class MaintenanceLog(models.Model):
    MAINTENANCE_TYPE_CHOICES = [
        ("preventive", "Preventive Maintenance"),
        ("corrective", "Corrective Maintenance"),
        ("calibration", "Sensor Calibration"),
        ("replacement", "Component Replacement"),
        ("software_update", "Software Update"),
    ]

    device = models.ForeignKey(
        BACnetDevice, on_delete=models.CASCADE, related_name="maintenance_logs"
    )

    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPE_CHOICES)
    scheduled_date = models.DateTimeField()
    completed_date = models.DateTimeField(null=True, blank=True)

    description = models.TextField()
    technicial_notes = models.TextField(blank=True)
    predicted_failure_date = models.DateTimeField(null=True, blank=True)
    confidence_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )

    is_completed = models.BooleanField(default=False)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        ordering = ["-scheduled_date"]
        verbose_name = "Maintenance Log"
        verbose_name_plural = "Maintenance Logs"
        indexes = [
            models.Index(fields=["device", "-scheduled_date"]),
            models.Index(fields=["is_completed"]),
        ]

    def __str__(self):
        status = "Completed" if self.is_completed else "Scheduled"
        return f"{self.device} - {self.maintenance_type} ({status})"

    def mark_completed(self, notes=""):
        self.is_completed = True
        self.completed_date = timezone.now()
        if notes:
            self.technician_notes = notes
        self.save()
