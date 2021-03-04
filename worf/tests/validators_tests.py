import pytest
from uuid import UUID

from django.core.exceptions import ValidationError
from django.test import RequestFactory

from worf.validators import ValidationMixin
from worf.views import AbstractBaseAPI
from django.db import models


# class DummyModel(models.Model):
#     id = models.CharField()
#     email = models.CharField()
#     phone = models.CharField()


class DummyAPI(ValidationMixin):
    # model = DummyModel

    def validate_phone(self, value):
        try:
            assert value == "(555) 555-5555"
        except AssertionError:
            raise ValidationError("{value} is not a valid phone number")
        return "+5555555555"


@pytest.fixture
def view():
    view = DummyAPI()
    view.bundle = {
        "id": "ce6a5b4f-599d-4442-8a74-d7a8d2b54854",
        "email": "something@example.com",
        "phone": "(555) 555-5555",
    }
    view.request = RequestFactory()
    return view


# def test_validate_bundle(view):
#     assert view.validate_bundle("id") == UUID("ce6a5b4f-599d-4442-8a74-d7a8d2b54854")
#     assert view.validate_bundle("email") == "something@example.com"
#     assert view.validate_bundle("phone") == "+5555555555"


def test_validate_uuid_passes(view):
    string = "ce6a5b4f-599d-4442-8a74-d7a8d2b54854"
    result = view.validate_uuid(string)
    assert result == UUID(string)


def test_validate_uuid_raises_error(view):
    string = "not-a-uuid"
    with pytest.raises(ValidationError):
        view.validate_uuid(string)


def test_validate_email_passes(view):
    email = "something@example.com"
    result = view.validate_email(email)
    assert email == result


def test_validate_email_raises_error(view):
    email = "fake.example@com"
    with pytest.raises(ValidationError):
        view.validate_email(email)


def test_validate_custom_field_passes(view):
    phone = "(555) 555-5555"
    assert view.validate_phone(phone) == "+5555555555"


def test_validate_custom_field_raises_error(view):
    phone = "invalid number"
    with pytest.raises(ValidationError):
        view.validate_phone(phone)


# def test_validate_skills_array(view):
#     invalid = None
#
#     with pytest.raises(ValidationError):
#         invalid = view.validate_skills_array(invalid)
#
#     valid_dict = dict(id=1, text="skill")
#     skills = [
#         dict(text="skill2"),
#         valid_dict,
#         True,
#         0,
#         [],
#         None,
#     ]
#
#     skills = view.validate_skills_array(skills)
#     assert skills == [valid_dict]
