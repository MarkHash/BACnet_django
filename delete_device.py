"""Quick script to delete virtual device 1001"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bacnet_project.settings")
django.setup()

from discovery.models import VirtualBACnetDevice  # noqa: E402

# Delete device 1001
deleted_count, _ = VirtualBACnetDevice.objects.filter(device_id=1001).delete()
print(f"✅ Deleted {deleted_count} device(s) with ID 1001")

# Show remaining devices
remaining = VirtualBACnetDevice.objects.all()
print(f"\nRemaining virtual devices: {remaining.count()}")
for device in remaining:
    print(f"  - Device {device.device_id}: {device.device_name}")
