from django.urls import include, path

from tests.views import DummyAPI, UserDetail, UserList

urlpatterns = [
    path("", DummyAPI.as_view()),
    path("users/", UserList.as_view()),
    path("users/<str:id>/", UserDetail.as_view()),
    path("<str:id>/", DummyAPI.as_view()),
]
