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
    @classmethod
    def write(cls):
        return [
            "username",
            "email",
        ]

    def read(self):
        return dict(
            username=self.model.username,
            lastLogin=self.model.last_login,
            dateJoined=self.model.date_joined,
            email=self.model.email,
        )


class UserAPI(DetailUpdateAPI):
    model = User
    serializer = UserSerializer
    permissions = [PublicEndpoint]
