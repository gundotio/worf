from urllib.parse import urlencode

from tests import fixture, register


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
            "django.contrib.sessions",
            "tests",
            "worf",
        ],
        MIDDLEWARE=[
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
        ],
        PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
        ROOT_URLCONF="tests.urls",
        SECRET_KEY="secret",
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "APP_DIRS": True,
            },
        ],
        TIME_ZONE="UTC",
        USE_I18N=False,
        USE_TZ=True,
        WORF_API_NAME="Test API",
        WORF_DEBUG=False,
    )

    django.setup()

    from tests.factories import (
        ProfileFactory,
        RoleFactory,
        SkillFactory,
        TagFactory,
        TaskFactory,
        TeamFactory,
        UserFactory,
    )

    register(ProfileFactory, "profile")
    register(RoleFactory, "role")
    register(SkillFactory, "skill")
    register(TagFactory, "tag")
    register(TaskFactory, "task")
    register(TeamFactory, "team")
    register(UserFactory, "user")


@fixture(name="admin_client")
def admin_client_fixture(db, admin_user):
    from worf.testing import ApiClient

    client = ApiClient()
    client.force_login(admin_user)
    return client


@fixture(name="client")
def client_fixture():
    from worf.testing import ApiClient

    return ApiClient()


@fixture(name="now")
def now_fixture():
    from django.utils import timezone

    return timezone.now


@fixture(name="url")
def url_fixture(url_params):
    def url(url, data={}):
        return f"{url}?{url_params(data)}" if data else url

    return url


@fixture(name="url_params")
def url_params_fixture(url_params__array_format):
    def url_params(data):
        if url_params__array_format == "comma":
            data = {
                key: ",".join(map(str, value)) if isinstance(value, list) else value
                for key, value in data.items()
            }
        return urlencode(data, True)

    return url_params


@fixture(name="url_params__array_format")
def url_params__array_format_fixture():
    return "repeat"


@fixture(name="user_client")
def user_client_fixture(db, user):
    from worf.testing import ApiClient

    client = ApiClient()
    client.force_login(user)
    return client
