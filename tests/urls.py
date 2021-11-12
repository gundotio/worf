from django.urls import include, path

from tests.views import (
    ProfileDetail,
    ProfileList,
    ProfileListSubSet,
    UserDetail,
    UserList,
)

urlpatterns = [
    path("profiles/", ProfileList.as_view()),
    path("profiles/subset/", ProfileListSubSet.as_view()),
    path("profiles/<str:id>/", ProfileDetail.as_view()),
    path("users/", UserList.as_view()),
    path("users/<str:id>/", UserDetail.as_view()),
]
