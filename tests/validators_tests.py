import pytest
from uuid import UUID

from django.core.exceptions import ValidationError
from django.test import RequestFactory

from tests.models import DummyModel
from tests.views import DummyAPI

test_uuid = "ce6a5b4f-599d-4442-8a74-d7a8d2b54854"
test_email = "something@example.com"
test_phone = "(555) 555-5555"


@pytest.fixture
@pytest.mark.django_db
def view():
    view = DummyAPI()
    view.bundle = {
        "id": test_uuid,
        "email": test_email,
        "phone": test_phone,
    }
    DummyModel.objects.create(id=UUID(test_uuid), email=test_email, phone=test_phone)
    view.request = RequestFactory().patch(f"/{test_uuid}/")
    view.kwargs = dict(id=test_uuid)
    return view


@pytest.mark.django_db
def test_validate_bundle(view):
    assert view.validate_bundle("id")
    assert view.validate_bundle("email")
    assert view.validate_bundle("phone")


@pytest.mark.django_db
def test_validate_uuid_accepts_str(view):
    string = "ce6a5b4f-599d-4442-8a74-d7a8d2b54854"
    result = view.validate_uuid(string)
    assert result == UUID(string)


@pytest.mark.django_db
def test_validate_uuid_accepts_uuid(view):
    uuid = UUID("ce6a5b4f-599d-4442-8a74-d7a8d2b54854")
    result = view.validate_uuid(uuid)
    assert result == uuid


@pytest.mark.django_db
def test_validate_uuid_raises_error(view):
    string = "not-a-uuid"
    with pytest.raises(ValidationError):
        view.validate_uuid(string)


@pytest.mark.django_db
def test_validate_email_passes(view):
    email = "something@example.com"
    result = view.validate_email(email)
    assert email == result


@pytest.mark.django_db
def test_validate_email_raises_error(view):
    email = "fake.example@com"
    with pytest.raises(ValidationError):
        view.validate_email(email)


@pytest.mark.django_db
def test_validate_custom_field_passes(view):
    phone = "(555) 555-5555"
    assert view.validate_phone(phone) == "+5555555555"


@pytest.mark.django_db
def test_validate_custom_field_raises_error(view):
    phone = "invalid number"
    with pytest.raises(ValidationError):
        view.validate_phone(phone)
