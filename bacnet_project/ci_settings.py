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
