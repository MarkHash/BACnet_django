import os

from .settings import *  # noqa: F401,F403

SECRET_KEY = os.environ.get("SECRET_KEY", "fallback-secret-key")
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
