from django.urls import include, path

from tests.views import (
    DummyAPI,
    ProfileDetail,
    ProfileList,
    ProfileListSubSet,
    UserDetail,
    UserList,
)

urlpatterns = [
    path("", DummyAPI.as_view()),
    path("profiles/", ProfileList.as_view()),
    path("profiles/subset/", ProfileListSubSet.as_view()),
    path("profiles/<str:id>/", ProfileDetail.as_view()),
    path("users/", UserList.as_view()),
    path("users/<str:id>/", UserDetail.as_view()),
    path("<str:id>/", DummyAPI.as_view()),
]
