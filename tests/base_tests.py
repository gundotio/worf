import pytest

from django.core.exceptions import ImproperlyConfigured
from django.test import RequestFactory
from worf.views import AbstractBaseAPI


def dummy_perm(self, request):
    return 201


class DummyAPI(AbstractBaseAPI):
    model = True
    permissions = [dummy_perm]


@pytest.fixture
def view():
    view = DummyAPI()
    view.request = RequestFactory()
    return view


def test_check_permissions(view):
    with pytest.raises(ImproperlyConfigured):
        view._check_permissions()
