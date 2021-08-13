from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from worf.permissions import PublicEndpoint
from worf.views import DetailUpdateAPI, ListAPI

from tests.models import DummyModel, Profile
from tests.serializers import ProfileSerializer, UserSerializer


class DummyAPI(DetailUpdateAPI):
    model = DummyModel
    permissions = [PublicEndpoint]

    def validate_phone(self, value):
        try:
            assert value == "(555) 555-5555"
        except AssertionError:
            raise ValidationError("{value} is not a valid phone number")
        return "+5555555555"


class ProfileList(ListAPI):
    model = Profile
    ordering = ["pk"]
    serializer = ProfileSerializer
    permissions = [PublicEndpoint]
    search_fields = {}
    filter_fields = [
        "tags",
    ]


class ProfileDetail(DetailUpdateAPI):
    model = Profile
    serializer = ProfileSerializer
    permissions = [PublicEndpoint]


class UserList(ListAPI):
    model = User
    ordering = ["pk"]
    serializer = UserSerializer
    permissions = [PublicEndpoint]
    search_fields = {
        "or": [
            "email",
            "username",
        ]
    }
    filter_fields = [
        "email",
        "date_joined__gte",
        "date_joined__lte",
    ]
    sort_fields = [
        "id",
        "date_joined",
    ]


class UserDetail(DetailUpdateAPI):
    model = User
    serializer = UserSerializer
    permissions = [PublicEndpoint]
