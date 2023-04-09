from django.contrib.auth.models import User
from django.urls import URLPattern

from tests import views
from tests.serializers import ProfileSerializer, UserSerializer
from worf.schema import SchemaGenerator
from worf.schema.openapi import SchemaMetadata


def test_get_api_endpoints():
    url_patterns = [
        URLPattern("^profiles/$", views.ProfileList.as_view()),
        URLPattern("users/<int:id>/", views.UserDetail.as_view()),
    ]
    schema_generator = SchemaGenerator(
        title="any title", base_url="http://localhost:8000", urlpatterns=url_patterns
    )
    endpoints = list(schema_generator.get_api_endpoints())
    endpoints = [repr(endpoint) for endpoint in endpoints]

    assert endpoints == [
        repr(expected_schema_metadata)
        for expected_schema_metadata in [
            SchemaMetadata(
                path="/profiles/",
                method="POST",
                description="post profiles",
                serializer=ProfileSerializer,
                is_list=True,
                model=views.Profile,
                tag="profiles",
            ),
            SchemaMetadata(
                path="/profiles/",
                method="GET",
                description="get profiles",
                serializer=ProfileSerializer,
                is_list=True,
                model=views.Profile,
                tag="profiles",
            ),
            SchemaMetadata(
                path="/users/{id}/",
                method="GET",
                description="get users[id]",
                serializer=UserSerializer(exclude=["date_joined"]),
                is_list=False,
                model=User,
                tag="users",
            ),
            SchemaMetadata(
                path="/users/{id}/",
                method="PUT",
                description="put users[id]",
                serializer=UserSerializer(exclude=["date_joined"]),
                is_list=False,
                model=User,
                tag="users",
            ),
            SchemaMetadata(
                path="/users/{id}/",
                method="PATCH",
                description="patch users[id]",
                serializer=UserSerializer(exclude=["date_joined"]),
                is_list=False,
                model=User,
                tag="users",
            ),
            SchemaMetadata(
                path="/users/{id}/",
                method="DELETE",
                description="delete users[id]",
                serializer=UserSerializer(exclude=["date_joined"]),
                is_list=False,
                model=User,
                tag="users",
            ),
        ]
    ]
