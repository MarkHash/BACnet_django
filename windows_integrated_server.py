"""
Windows Integrated Server for BACnet Django Application

This module provides a Windows-native deployment solution that combines Django web
server
with native BACnet operations in a single process. It solves Docker Desktop networking
limitations on Windows where containers cannot access the host network required for
BACnet UDP broadcast discovery.

Architecture:
- Main Thread: Django development server (web interface)
- Background Thread: BACnet worker with periodic device discovery and data collection
- Database: Connects to PostgreSQL running in Docker container
- Networking: Full Windows host network access for BACnet operations

Key Features:
- Automatic platform validation (Windows-only)
- Periodic BACnet device discovery (every 30 minutes)
- Continuous data collection from discovered devices (every 5 minutes)
- Comprehensive error handling and recovery
- Real-time status monitoring and logging
- Graceful shutdown with proper cleanup

Usage:
    # Start Docker infrastructure (Windows)
    docker-compose -f docker-compose.windows.yml up -d

    # Run integrated server
    python windows_integrated_server.py

    # Access web interface at http://127.0.0.1:8000

This solution maintains the same functionality as Linux/Mac Docker deployments while
providing native Windows network access for reliable BACnet communication.
"""

import os
import platform
import sys
import threading
import time

# Configure Django settings before importing models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bacnet_project.settings")

import django  # noqa: E402

django.setup()

from django.core.management import execute_from_command_line  # noqa: E402
from django.db import connection  # noqa: E402

from discovery.constants import BACnetConstants  # noqa: E402
from discovery.services import get_unified_bacnet_service  # noqa: E402

DISCOVERY_INTERVAL = 1800  # 30 minutes
READINGS_INTERVAL = 300  # 5 minutes
WORKER_CHECK_INTERVAL = 30  # 30 seconds
ERROR_RETRY_INTERVAL = 60  # 1 minute


def run_device_discovery():
    try:
        service = get_unified_bacnet_service()
        devices = service.discover_devices()
        print(f"✅ Discovery completed: {len(devices)} devices found")

        return True
    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        return False


def run_collect_recordings():
    try:
        service = get_unified_bacnet_service()
        readings = service.collect_all_readings()
        print(f"✅ Readings completed: {len(readings)} readings collected")
        return True

    except Exception as e:
        print(f"❌ Readings failed: {e}")
        return False


def bacnet_worker():
    """Windows-only background BACnet worker with periodic scheduling"""
    print("🪟 Windows BACnet worker starting...")
    print("📡 Device discovery: every 1800 seconds (30 minutes)")
    print("📊 Readings collection: every 300 seconds (5 minutes)")
    print("🔄 Checking for tasks every 30 seconds")

    last_discovery = 0
    last_readings = 0

    while True:
        try:
            current_time = time.time()

            if current_time - last_discovery >= DISCOVERY_INTERVAL:
                print(
                    f"🔍 Running scheduled device discovery... "
                    f"({time.strftime('%H:%M:%S')})"
                )

                if run_device_discovery():
                    last_discovery = current_time

            if (
                current_time - last_readings
                >= BACnetConstants.COLLECTION_INTERVAL_SECONDS
            ):
                print(
                    f"📊 Running scheduled readings collection... "
                    f"({time.strftime('%H:%M:%S')})"
                )

                if run_collect_recordings():
                    last_readings = current_time
            time.sleep(WORKER_CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\n⏹️ BACnet worker stopping...")
            break
        except Exception as e:
            print(f"🚨 Worker error: {e}")
            time.sleep(60)


def validate_prerequisites():
    """Validate all prerequisites before starting"""
    errors = []

    if platform.system() != "Windows":
        errors.append("This server is only for Windows")

    try:
        django.setup()
    except Exception as e:
        errors.append(f"Django setup failed: {e}")

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception as e:
        errors.append(f"Database connection failed: {e}")

    return errors


def display_server_info():
    """Display server configuration and info"""
    print("📋 This server combines:")
    print("   • Django web interface (port 8000)")
    print("   • Native BACnet worker (Windows host network)")
    print()
    print("🔧 Prerequisites:")
    print(
        "   • Docker services running: docker-compose -f "
        "docker-compose.windows.yml up -d"
    )
    print("   • Environment variables configured (.env file)")
    print("=" * 60)


def main():
    print("=" * 60)
    print("🪟 Windows Integrated BACnet Server Starting...")
    print("=" * 60)

    errors = validate_prerequisites()
    if errors:
        for error in errors:
            print(f"❌ {error}")
        print("\n💡 Please fix the above issues and try again")
        sys.exit(1)

    display_server_info()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bacnet_project.settings")

    print()
    print("🚀 Starting services...")

    print("🔄 Starting BACnet worker thread...")
    worker_thread = threading.Thread(target=bacnet_worker, daemon=True)
    worker_thread.start()
    print("✅ BACnet worker thread started")

    # Start Django development server in main thread
    print("🌐 Starting Django web server...")
    print("📍 Access your application at: http://localhost:8000")
    print("⏹️  Press Ctrl+C to stop both services")
    print()

    try:
        execute_from_command_line(["manage.py", "runserver", "0.0.0.0:8000"])
    except KeyboardInterrupt:
        print("\n👋 Shutting down Windows Integrated BACnet Server...")
        print("✅ Server stopped successfully")


if __name__ == "__main__":
    main()
