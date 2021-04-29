from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from worf.permissions import PublicEndpoint
from worf.serializers import Serializer
from worf.views import DetailUpdateAPI

from tests.models import DummyModel


class DummyAPI(DetailUpdateAPI):
    model = DummyModel
    permissions = [PublicEndpoint]

    def validate_phone(self, value):
        try:
            assert value == "(555) 555-5555"
        except AssertionError:
            raise ValidationError("{value} is not a valid phone number")
        return "+5555555555"


class UserSerializer(Serializer):
    def read(self, model):
        return dict(
            username=model.username,
            lastLogin=model.last_login,
            dateJoined=model.date_joined,
            email=model.email,
        )

    def write(self):
        return [
            "username",
            "email",
        ]


class UserAPI(DetailUpdateAPI):
    model = User
    serializer = UserSerializer
    permissions = [PublicEndpoint]
