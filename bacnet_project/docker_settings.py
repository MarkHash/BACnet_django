import os

import dj_database_url

from .settings import *  # noqa: F401,F403

# Override Windows detection for containers
# Check HOST_OS environment variable instead of platform.system()
IS_WINDOWS_HOST = os.environ.get("HOST_OS") == "Windows"

if IS_WINDOWS_HOST:
    print("🪟 Windows host detected in container")
else:
    print("🐧 Linux/Mac host detected in container")

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
