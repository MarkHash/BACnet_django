import os

import django

from discovery.services import BACnetService

# Configure Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bacnet_project.docker_settings")
django.setup()


def print_callback(message):
    print(f"CALLBACK: {message}")


service = BACnetService(callback=print_callback)

# time.sleep(10)
devices = service.discover_devices(mock_mode=True)
print(f"Discovery completed: {devices}")
