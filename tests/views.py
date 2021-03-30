from django.core.exceptions import ValidationError

from tests.models import DummyModel
from worf.validators import ValidationMixin
from worf.views import DetailUpdateAPI


class DummyAPI(DetailUpdateAPI, ValidationMixin):
    model = DummyModel

    def validate_phone(self, value):
        try:
            assert value == "(555) 555-5555"
        except AssertionError:
            raise ValidationError("{value} is not a valid phone number")
        return "+5555555555"
