from django.urls import include, path

from tests.views import DummyAPI, UserAPI

urlpatterns = [
    path("", DummyAPI.as_view()),
    path("<str:id>/", DummyAPI.as_view()),
    path("user/<str:id>/", UserAPI.as_view()),
]
