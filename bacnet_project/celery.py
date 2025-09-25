"""
Celery configuration for BACnet Django project.

This module configures Celery for background task processing including:
- BACnet device discovery and data collection tasks
- Periodic task scheduling via Celery Beat
- Integration with Django settings and Redis broker

The app auto-discovers tasks from all Django apps and uses docker_settings
for containerized deployment with conditional Windows support.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bacnet_project.docker_settings")

app = Celery("bacnet_project")
app.config_from_object("django.conf:settings", namespace="CELERY")
# app.autodiscover_tasks(['discovery'])
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
