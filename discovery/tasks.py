"""
BACnet Celery Background Tasks - Simplified Core Version

This module defines Celery tasks for basic BACnet operations that run in the
background. These tasks handle periodic device discovery and data collection
for building automation monitoring.

Tasks:
- discover_devices_task: Performs network-wide BACnet device discovery
- collect_readings_task: Collects current values from all active device points

Platform Support:
- Linux/Mac: Tasks run in Docker containers via Celery Beat scheduling
- Windows: Tasks are executed by windows_integrated_server.py for native
  network
  access

The tasks are designed to be idempotent and handle failures gracefully with
comprehensive logging for monitoring and debugging.
"""

import logging
import subprocess
import sys

from celery import shared_task
from django.conf import settings

from .services import BACnetService

logger = logging.getLogger(__name__)


@shared_task(bind=True, queue="bacnet")
def discover_devices_task(self, mock_mode=False):
    try:
        if getattr(settings, "IS_WINDOWS_HOST", False):
            cmd = [sys.executable, "manage.py", "discover_devices"]
            if mock_mode:
                cmd.append("--mock")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd="/host_app",
            )
            if result.returncode == 0:
                return {"success": True, "output": result.stdout}
            else:
                return {"success": False, "output": result.stdout}

        else:
            service = BACnetService()
            devices = service.discover_devices(mock_mode=mock_mode)
            return {
                "success": True,
                "devices_found": len(devices) if devices else 0,
            }
    except Exception as e:
        logger.error(f"Device discovery task failed: {e}")
        return {"error": str(e)}


@shared_task(bind=True, queue="bacnet")
def collect_readings_task(self):
    try:
        if getattr(settings, "IS_WINDOWS_HOST", False):
            cmd = [sys.executable, "manage.py", "collect_readings"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd="/host_app",
            )
            if result.returncode == 0:
                return {"success": True, "output": result.stdout}
            else:
                return {"success": False, "output": result.stdout}

        else:
            service = BACnetService()
            results = service.collect_all_readings()
            return {
                "success": True,
                "readings_collected": results.get("readings_collected", 0),
            }
    except Exception as e:
        return {"success": False, "error": str(e)}
