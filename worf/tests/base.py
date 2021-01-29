from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, RequestFactory
from worf.views import AbstractBaseAPI


class AbstractBaseAPITests(TestCase):
    def test_check_permissions(self):
        def dummy_perm(self, request):
            return 201

        class DummyAPI(AbstractBaseAPI):
            model = True
            permissions = [dummy_perm]

        inst = DummyAPI()
        inst.request = RequestFactory()
        with self.assertRaises(ImproperlyConfigured):
            inst._check_permissions()
