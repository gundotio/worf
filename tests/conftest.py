import pytest
from pytest_factoryboy import register


def pytest_configure():
    """Initialize Django settings."""
    import django
    from django.conf import settings

    settings.configure(
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": "db.sqlite3",
            }
        },
        INSTALLED_APPS=[
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "tests",
            "worf",
        ],
        PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
        ROOT_URLCONF="tests.urls",
        SECRET_KEY="secret",
        TEMPLATES = [
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "APP_DIRS": True,
            },
        ],
        TIME_ZONE="UTC",
        USE_I18N=False,
        USE_L10N=False,
        USE_TZ=True,
        WORF_API_NAME="Test API",
        WORF_DEBUG=True,
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


@pytest.fixture(name="admin_client")
def admin_client_fixture(db, admin_user):
    from worf.testing import ApiClient

    client = ApiClient()
    client.force_login(admin_user)
    return client


@pytest.fixture(name="client")
def client_fixture():
    from worf.testing import ApiClient

    return ApiClient()


@pytest.fixture(name="now")
def now_fixture():
    from django.utils import timezone

    return timezone.now()


@pytest.fixture(name="user_client")
def user_client_fixture(db, user):
    from worf.testing import ApiClient

    client = ApiClient()
    client.force_login(user)
    return client
