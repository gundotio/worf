from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.db.models import F, Value
from django.db.models.functions import Concat

from worf.permissions import PublicEndpoint
from worf.views import CreateAPI, DeleteAPI, DetailAPI, ListAPI, UpdateAPI

from tests.models import Profile
from tests.serializers import ProfileSerializer, UserSerializer


class ProfileList(CreateAPI, ListAPI):
    model = Profile
    queryset = Profile.objects.annotate(
        first_name=F("user__first_name"),
        last_name=F("user__last_name"),
        name=Concat("first_name", Value(" "), "last_name"),
        date_joined=F("user__date_joined"),
    )
    ordering = ["pk"]
    serializer = ProfileSerializer
    permissions = [PublicEndpoint]
    search_fields = []
    filter_fields = [
        "first_name",
        "first_name__icontains",
        "last_name",
        "name",
        "name__icontains",
        "name__in",
        "date_joined__gte",
        "tags",
        "tags__in",
    ]


class ProfileListSubSet(ProfileList):
    queryset = ProfileList.queryset.none()


class ProfileDetail(DeleteAPI, UpdateAPI, DetailAPI):
    model = Profile
    serializer = ProfileSerializer
    permissions = [PublicEndpoint]

    def validate_phone(self, value):
        try:
            assert value == "(555) 555-5555"
        except AssertionError:
            raise ValidationError("Field phone is not a valid phone number")
        return "+5555555555"


class UserList(CreateAPI, ListAPI):
    model = User
    ordering = ["pk"]
    serializer = UserSerializer(only=[
        "username",
        "date_joined",
        "email",
    ])
    permissions = [PublicEndpoint]
    filter_fields = [
        "email",
        "date_joined__gte",
        "date_joined__lte",
    ]
    search_fields = [
        "email",
        "username",
    ]
    sort_fields = [
        "id",
        "date_joined",
    ]


class UserDetail(UpdateAPI, DetailAPI):
    model = User
    serializer = UserSerializer
    permissions = [PublicEndpoint]
