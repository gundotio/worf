from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from worf.permissions import PublicEndpoint
from worf.serializers import Serializer
from worf.views import DetailUpdateAPI, ListAPI

from tests.models import DummyModel, Profile


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

class ProfileSerializer(Serializer):
    def read(self, model):
        return dict(
            username=model.user.username,
            email=model.user.email,
            tags=[t.api() for t in model.tags.all()],
        )

    def write(self):
        return [
            "tags",
        ]


class UserDetail(DetailUpdateAPI):
    model = User
    serializer = UserSerializer
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

class ProfileList(ListAPI):
    model = Profile
    ordering = ["pk"]
    serializer = ProfileSerializer
    permissions = [PublicEndpoint]
    search_fields = {}
    filter_fields = [
        "tags",
    ]
    
