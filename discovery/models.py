from django.db import models
from django.utils import timezone

# Create your models here.
class BACnetDevice(models.Model):
    device_id = models.IntegerField(unique=True, help_text="BACnet device instance number")
    address = models.CharField(max_length=50, help_text="IP address of device")
    vendor_id = models.IntegerField(help_text="BACnet vendor ID")

    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now_add=True)

    is_online = models.BooleanField(default=True)
    points_read = models.BooleanField(default=True)

    class Meta:
        ordering = ['device_id']
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
        related_name='points',
        help_text="Device this point belongs to"
    )

    object_type = models.CharField(max_length=50, help_text="BACnet object type")
    instance_number = models.CharField(max_length=50, help_text="BACnet instance number")
    identifier = models.CharField(max_length=50, help_text="Full identifier")

    object_name = models.CharField(max_length=200, blank=True, help_text="Human-readable name")
    description = models.TextField(blank=True, help_text="Point description")

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['object_type', 'instance_number']
        unique_together = ['device', 'object_type', 'instance_number']
        verbose_name = "BACnet Point"
        verbose_name_plural = "BACnet Points"

    def __str__(self):
        return f"{self.identifier} on {self.device}"