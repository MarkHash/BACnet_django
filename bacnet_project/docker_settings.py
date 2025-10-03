import os

import dj_database_url

from discovery.constants import BACnetConstants

from .settings import *  # noqa: F401,F403

# Override Windows detection for containers
# Check HOST_OS environment variable instead of platform.system()
IS_WINDOWS_HOST = os.environ.get("HOST_OS") == "Windows"

if IS_WINDOWS_HOST:
    print("🪟 Windows host detected in container: BACnet tasks will use subprocess")
else:
    print(
        "🐧 Linux/Mac host detected in container: BACnet tasks will use direct service"
    )

SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-secret-key")
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("POSTGRES_DB", "bacnet_django"),
            "USER": os.environ.get("POSTGRES_USER", "bacnet_user"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "password"),
            "HOST": "db",
            "PORT": "5432",
        }
    }

DEBUG = os.environ.get("DEBUG", "0") == "1"

ALLOWED_HOSTS = ["*"]

STATIC_URL = "/static/"
STATIC_ROOT = "/app/staticfiles"

# Debug confirmation
print(f"🐳 DOCKER SETTINGS - DEBUG: {DEBUG}, DB HOST: {DATABASES['default']['HOST']}")

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "discovery": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
        },
    },
}


CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/1")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/1")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Australia/Melbourne"
CELERY_ENABLE_UTC = False

CELERY_BEAT_SCHEDULE = {
    "calculate-hourly-stats": {
        "task": "discovery.tasks.calculate_hourly_stats",
        "schedule": 3600.0,
    },
    "calculate-daily-stats": {
        "task": "discovery.tasks.calculate_daily_stats",
        "schedule": 86400.0,
    },
}

if not IS_WINDOWS_HOST:
    CELERY_BEAT_SCHEDULE.update(
        {
            "discover-devices": {
                "task": "discovery.tasks.discover_devices_task",
                "schedule": 1800.0,
                "kwargs": {"mock_mode": True},
            },
            "collect-readings": {
                "task": "discovery.tasks.collect_readings_task",
                "schedule": BACnetConstants.COLLECTION_INTERVAL_SECONDS,
            },
        }
    )
    print("🐧 Linux/Mac: BACnet tasks added to Celery Beat schedule")
else:
    print("🪟 Windows: BACnet tasks will be handled by integrated server")
