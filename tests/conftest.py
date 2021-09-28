import pytest
from pytest_factoryboy import register

import django
from django.conf import settings
from django.utils import timezone


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

    from tests.factories import (
        ProfileFactory,
        RoleFactory,
        SkillFactory,
        TagFactory,
        TeamFactory,
        UserFactory,
    )

    register(ProfileFactory, "profile")
    register(RoleFactory, "role")
    register(SkillFactory, "skill")
    register(TagFactory, "tag")
    register(TeamFactory, "team")
    register(UserFactory, "user")


@pytest.fixture(name="now")
def now_fixture():
    return timezone.now()


@pytest.fixture(name="profile_url")
def profile_url_fixture(profile):
    return f"/profiles/{profile.pk}/"


@pytest.fixture(name="user_url")
def user_url_fixture(user):
    return f"/users/{user.pk}/"
