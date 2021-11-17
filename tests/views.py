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
        name=Concat("user__first_name", Value(" "), "user__last_name"),
        date_joined=F("user__date_joined"),
    )
    ordering = ["pk"]
    serializer = ProfileSerializer
    permissions = [PublicEndpoint]
    search_fields = []
    filter_fields = [
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
            raise ValidationError("{value} is not a valid phone number")
        return "+5555555555"


class UserList(ListAPI):
    model = User
    ordering = ["pk"]
    serializer = UserSerializer
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
