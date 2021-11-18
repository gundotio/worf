from django.core.exceptions import ImproperlyConfigured

from worf.lookups import FindInstance
from worf.views.base import AbstractBaseAPI
from worf.views.update import UpdateAPI


class DetailAPI(FindInstance, AbstractBaseAPI):
    detail_serializer = None

    def get(self, request, *args, **kwargs):
        return self.render_to_response()

    def get_serializer(self):
        if self.detail_serializer and self.request.method == "GET":
            return self.detail_serializer()
        return super().get_serializer()

    def serialize(self):
        """Return the model api, used for responses."""
        serializer = self.get_serializer()
        payload = serializer.read(self.get_instance())
        if not isinstance(payload, dict):
            raise ImproperlyConfigured(f"{serializer} did not return a dictionary")
        return payload


class DetailUpdateAPI(UpdateAPI, DetailAPI):
    def patch(self, request, *args, **kwargs):
        self.update()
        return self.get(request)
