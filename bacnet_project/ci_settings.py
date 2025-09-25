"""
CI-specific Django settings for automated testing pipelines.

This configuration is used by GitHub Actions, GitLab CI, or other CI/CD systems.
It provides:
- Test database configuration with PostgreSQL
- Faster MD5 password hashing for test performance
- Production-like settings (DEBUG=False) for realistic testing

Usage: python manage.py test --settings=bacnet_project.ci_settings
"""

from .settings import *  # noqa: F401,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "bacnet_django_test",
        "USER": "postgres",
        "PASSWORD": "postgres_test_password",
        "HOST": "localhost",
        "PORT": "5432",
    }
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

DEBUG = False

ALLOWED_HOSTS = ["*"]
