import factory
from django.test import TestCase

from discovery.models import BACnetDevice, BACnetPoint


class BACnetDeviceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BACnetDevice

    device_id = factory.Sequence(lambda n: 100 + n)
    address = factory.Sequence(lambda n: f"192.168.1.{100 + n}")
    vendor_id = 123
    is_online = True
    points_read = True


class BACnetPointFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BACnetPoint

    device = factory.SubFactory(BACnetDeviceFactory)
    object_type = "analogInput"
    instance_number = factory.Sequence(lambda n: n)
    identifier = factory.LazyAttribute(
        lambda obj: f"{obj.object_type}:{obj.instance_number}"
    )


class BaseTestCase(TestCase):
    def setUp(self):
        self.device = BACnetDeviceFactory()
        self.point = BACnetPointFactory(device=self.device)
