from uuid import uuid4

import pytest

from django.core.exceptions import ValidationError

from tests.models import Profile

uuid = uuid4()
email = "something@example.com"
phone = "(555) 555-5555"


@pytest.fixture(name="profile_instance")
def profile_instance_fixture(db, profile_factory, rf):
    profile = profile_factory.create(id=1, email=email, phone=phone)
    return profile


@pytest.fixture(name="profile_view")
def profile_view_fixture(db, now, profile_instance, rf):
    from tests.views import ProfileDetail

    view = ProfileDetail()
    view.set_bundle(
        dict(
            id=str(uuid),
            email=email,
            phone=phone,
            boolean=True,
            integer=123,
            json=dict(something=True),
            positive_integer=123,
            slug="something",
            small_integer=123,
            recovery_email=email,
            recovery_phone=phone,
            last_active=now().date().isoformat(),
            created_at=now().isoformat(),
        )
    )
    view.request = rf.patch(f"/{uuid}/")
    view.kwargs = dict(id=str(uuid))
    return view


def test_strip_fields(profile_view):
    profile_view.set_bundle(dict(slug="te\x00st "))
    profile_view.validate_bundle("slug")
    assert profile_view.bundle["slug"] == "test"

    profile_view.secure_fields = ["slug"]

    profile_view.set_bundle(dict(slug="te\x00st "))
    profile_view.validate_bundle("slug")
    assert profile_view.bundle["slug"] == "te\x00st "


def test_validate_bundle(profile_view):
    profile_view.validate_bundle("id")
    profile_view.validate_bundle("email")
    profile_view.validate_bundle("phone")
    profile_view.validate_bundle("boolean")
    profile_view.validate_bundle("integer")
    profile_view.validate_bundle("json")
    profile_view.validate_bundle("positive_integer")
    profile_view.validate_bundle("slug")
    profile_view.validate_bundle("small_integer")
    profile_view.validate_bundle("recovery_email")
    profile_view.validate_bundle("last_active")
    profile_view.validate_bundle("created_at")


def test_validate_bundle_accepts_blanks(profile_view):
    profile_view.set_bundle(dict(recovery_email=""))
    profile_view.validate_bundle("recovery_email")


def test_validate_bundle_accepts_nulls(profile_view):
    profile_view.set_bundle(dict(recovery_email=None))
    profile_view.validate_bundle("recovery_email")


def test_validate_bundle_raises_invalid_booleans(profile_view):
    profile_view.set_bundle(dict(boolean="nooo"))

    with pytest.raises(ValidationError) as e:
        profile_view.validate_bundle("boolean")

    assert "Field boolean accepts a boolean, got nooo" in str(e.value)


def test_validate_bundle_raises_invalid_fields(profile_view):
    profile_view.set_bundle(dict(invalid_field=email))

    with pytest.raises(ValidationError) as e:
        profile_view.validate_bundle("invalid_field")

    assert "invalid_field is not editable" in str(e.value)


def test_validate_bundle_raises_read_only_fields(profile_view):
    with pytest.raises(ValidationError) as e:
        profile_view.validate_bundle("recovery_phone")

    assert "recovery_phone is not editable" in str(e.value)


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


def test_validate_required_fields_passes(profile_view, profile_instance):
    profile_view.validate_required_fields(Profile, profile_instance)


def test_validate_required_fields_raises_error(profile_view, profile_instance):
    no_phone_bundle = {**profile_view.bundle, "phone": None}
    profile_view.bundle = no_phone_bundle
    profile_instance.phone = None
    with pytest.raises(ValidationError):
        profile_view.validate_required_fields(Profile, profile_instance)
