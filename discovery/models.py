from django.db import models
from django.utils import timezone


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
    points_read = models.BooleanField(default=True)

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
            return "No reading"

        value = self.present_value

        if self.data_type == "real":
            try:
                float_val = float(value)
                value = f"{float_val:.2f}"
            except ValueError:
                pass
        elif self.data_type == "boolean":
            value = (
                "ON" if str(value).lower() in ["true", "1", "on", "active"] else "OFF"
            )

        if self.units:
            return f"{value} {self.units}"
        return value

    @property
    def is_readable(self):
        readable_types = [
            "analogInput",
            "analogOutput",
            "analogValue",
            "binaryInput",
            "binaryOutput",
            "binaryValue",
            "multiStateInput",
            "multiStateOutput",
            "multiStateValue",
        ]
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
    read_time = models.DateTimeField(
        auto_now_add=True, help_text="When reading was taken"
    )

    quality = models.CharField(
        max_length=50, blank=True, help_text="Reading quality (good, bad, uncertain)"
    )
    priority = models.IntegerField(null=True, blank=True, help_text="Reading priority")

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
