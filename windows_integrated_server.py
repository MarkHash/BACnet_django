"""
Windows Django Server for BACnet Application (Simplified Architecture)

This module provides a Windows-native Django development server that connects to
PostgreSQL running in Docker. For the simplified architecture without Celery.

Architecture:
- Django development server (web interface)
- Database: Connects to PostgreSQL running in Docker container
- Virtual Devices: Managed separately via `python manage.py run_virtual_devices`
- Networking: Full Windows host network access for BACnet operations

Key Features:
- Automatic platform validation (Windows-only)
- Database connection verification
- Simple Django web server for BACnet device management

Usage:
    # Start Docker database (Windows)
    docker-compose -f docker-compose.windows.yml up -d db

    # Terminal 1: Run Django web server
    python windows_integrated_server.py

    # Terminal 2: Run virtual device server (optional)
    python manage.py run_virtual_devices

    # Access web interface at http://127.0.0.1:8000

This simplified solution provides the web interface for managing BACnet devices
while keeping virtual device management in a separate process.
"""

import os
import platform
import sys

# Configure Django settings before importing models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bacnet_project.settings")

import django  # noqa: E402

django.setup()

from django.core.management import execute_from_command_line  # noqa: E402
from django.db import connection  # noqa: E402


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
    print("📋 This server provides:")
    print("   • Django web interface (port 8000)")
    print("   • BACnet device management via web UI")
    print()
    print("🔧 Prerequisites:")
    print("   • Docker database running: docker-compose -f ")
    print("     docker-compose.windows.yml up -d db")
    print("   • Environment variables configured (.env file)")
    print()
    print("💡 For virtual devices, run in separate terminal:")
    print("   python manage.py run_virtual_devices")
    print("=" * 60)


def main():
    print("=" * 60)
    print("🪟 Windows Django Server Starting...")
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
    print("🚀 Starting Django web server...")
    print("📍 Access your application at: http://localhost:8000")
    print("⏹️  Press Ctrl+C to stop the server")
    print()

    try:
        execute_from_command_line(["manage.py", "runserver", "0.0.0.0:8000"])
    except KeyboardInterrupt:
        print("\n👋 Shutting down Django server...")
        print("✅ Server stopped successfully")


if __name__ == "__main__":
    main()
