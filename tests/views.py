from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import F, Prefetch, Value
from django.db.models.functions import Concat

from tests.models import Profile
from tests.serializers import ProfileSerializer, UserSerializer
from worf.exceptions import AuthenticationError
from worf.permissions import Authenticated, PublicEndpoint, Staff
from worf.views import ActionAPI, CreateAPI, DeleteAPI, DetailAPI, ListAPI, UpdateAPI


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
    include_fields = {
        "skills": Prefetch("skills"),
        "team": "team",
    }


class ProfileDetail(ActionAPI, DeleteAPI, UpdateAPI, DetailAPI):
    model = Profile
    serializer = ProfileSerializer
    permissions = [PublicEndpoint]
    actions = [
        "resubscribe",
        "subscribe",
        "unsubscribe",
    ]

    def resubscribe(self, request, *args, **kwargs):
        profile = self.get_instance()
        profile.subscribe(user=request.user)
        return profile

    def validate_phone(self, value):
        try:
            assert value == "(555) 555-5555"
        except AssertionError:
            raise ValidationError("Field phone is not a valid phone number")
        return "+5555555555"


class StaffDetail(ProfileDetail):
    permissions = [Authenticated, Staff]


class UserList(CreateAPI, ListAPI):
    model = User
    ordering = ["pk"]
    serializer = UserSerializer(
        only=[
            "id",
            "username",
            "date_joined",
            "email",
        ]
    )
    permissions = [PublicEndpoint]
    filter_fields = [
        "id",
        "email",
        "date_joined__gte",
        "date_joined__lte",
    ]
    search_fields = [
        "id",
        "email",
        "username",
    ]
    sort_fields = [
        "id",
        "date_joined",
    ]


class UserDetail(UpdateAPI, DetailAPI):
    model = User
    serializer = UserSerializer(exclude=["date_joined"])
    permissions = [PublicEndpoint]


class UserSelf(DetailAPI):
    model = User
    serializer = UserSerializer
    permissions = [PublicEndpoint]

    def get_instance(self):
        if not self.request.user.is_authenticated:
            raise AuthenticationError("Log in with your username and password")
        return self.request.user
