from django.urls import include, path

from tests.views import DummyAPI

urlpatterns = [
    path("api/v1/", include(
        path("<str:id>/", DummyAPI.as_view()),
    ))
]
