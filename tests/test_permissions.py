import pytest

from django.contrib.auth.models import AnonymousUser, User

from worf.exceptions import AuthenticationError, NotFound
from worf.permissions import Authenticated, PublicEndpoint, Staff


def test_authenticated(db, rf):
    permission = Authenticated()
    request = rf.get("/")
    request.user = AnonymousUser()

    with pytest.raises(AuthenticationError):
        assert permission(request) is None

    request.user = User.objects.create(username="test", password="test")
    assert permission(request) is None


def test_public_endpoint(db, rf):
    permission = PublicEndpoint()
    request = rf.get("/")
    request.user = AnonymousUser()
    assert permission(request) is None
    request.user = User.objects.create(username="test", password="test")
    assert permission(request) is None


def test_staff(db, rf):
    permission = Staff()
    request = rf.get("/")
    request.user = AnonymousUser()

    with pytest.raises(NotFound):
        assert permission(request) is None

    request.user = User.objects.create(username="test", password="test")

    with pytest.raises(NotFound):
        assert permission(request) is None

    request.user.is_staff = True
    request.user.save()
    permission(request)
