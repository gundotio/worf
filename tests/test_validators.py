import pytest

from uuid import uuid4

from django.core.exceptions import ValidationError

uuid = uuid4()
email = "something@example.com"
phone = "(555) 555-5555"


@pytest.fixture(name="profile_view")
def profile_view_fixture(db, profile_factory):
    from django.test import RequestFactory

    from tests.views import ProfileDetail

    profile_factory.create(email=email, phone=phone)
    view = ProfileDetail()
    view.bundle = {
        "id": str(uuid),
        "email": email,
        "phone": phone,
    }
    view.request = RequestFactory().patch(f"/{uuid}/")
    view.kwargs = dict(id=str(uuid))
    view.serializer = None
    return view


def test_validate_bundle(profile_view):
    assert profile_view.validate_bundle("id")
    assert profile_view.validate_bundle("email")
    assert profile_view.validate_bundle("phone")


def test_validate_uuid_accepts_str(profile_view):
    assert profile_view.validate_uuid(str(uuid)) == uuid


def test_validate_uuid_accepts_uuid(profile_view):
    assert profile_view.validate_uuid(uuid) == uuid


def test_validate_uuid_raises_error(profile_view):
    with pytest.raises(ValidationError):
        profile_view.validate_uuid("not-a-uuid")


def test_validate_email_passes(profile_view):
    assert profile_view.validate_email(email) == email


def test_validate_email_raises_error(profile_view):
    with pytest.raises(ValidationError):
        profile_view.validate_email("fake.example@com")


def test_validate_custom_field_passes(profile_view):
    assert profile_view.validate_phone(phone) == "+5555555555"


def test_validate_custom_field_raises_error(profile_view):
    with pytest.raises(ValidationError):
        profile_view.validate_phone("invalid number")
