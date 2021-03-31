import pytest

from django.contrib.auth.models import AnonymousUser, User
from django.test import RequestFactory

from worf.permissions import Authenticated, Staff
from worf.exceptions import HTTP401, HTTP404

factory = RequestFactory()


@pytest.mark.django_db
def test_authenticated():
    request = factory.get("/")

    request.user = AnonymousUser()
    assert isinstance(Authenticated(None, request), HTTP401)

    request.user = User.objects.create(username="test", password="test")
    assert Authenticated(None, request) == 200


@pytest.mark.django_db
def test_staff():
    request = factory.get("/")

    request.user = AnonymousUser()
    assert isinstance(Staff(None, request), HTTP404)

    request.user = User.objects.create(username="test", password="test")
    assert isinstance(Staff(None, request), HTTP404)

    request.user.is_staff = True
    request.user.save()
    assert Staff(None, request) == 200
