import pytest

import django
from django.conf import settings


def pytest_configure():
    """Initialize Django settings."""
    settings.configure(
        SECRET_KEY="secret",
        DEBUG=True,
        INSTALLED_APPS=[
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "django.contrib.staticfiles",
            "tests",
            "worf",
        ],
        MIDDLEWARE=[
            "django.middleware.common.CommonMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
        ],
        ROOT_URLCONF="tests.urls",
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": "db.sqlite3",
            }
        },
        PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
        TIME_ZONE="UTC",
        USE_I18N=True,
        USE_L10N=True,
        USE_TZ=True,
        STATIC_URL="/static/",
    )

    django.setup()


@pytest.fixture(name="user")
def user_fixture(django_user_model):
    return django_user_model.objects.create_user(username="test", password="password")
