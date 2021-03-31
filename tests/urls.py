from django.urls import include, path

from tests.views import DummyAPI

urlpatterns = [
    path("", DummyAPI.as_view()),
    path("<str:id>/", DummyAPI.as_view()),
]
