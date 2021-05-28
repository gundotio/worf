from django.core.exceptions import ImproperlyConfigured

from worf.views.base import AbstractBaseAPI
from worf.shortcuts import get_instance_or_http404


class DetailAPI(AbstractBaseAPI):
    lookup_field = "id"
    lookup_url_kwarg = "id"
    instance = None

    def get(self, request, *args, **kwargs):
        return self.render_to_response()

    def serialize(self):
        """Return the model api, used for responses."""
        serializer = self.get_serializer()
        payload = serializer.read(self.get_instance())
        if not isinstance(payload, dict):
            raise ImproperlyConfigured(f"{serializer} did not return a dictionary")
        return payload

    def get_instance(self):
        # TODO support multiple lookup_fields
        self.lookup_kwargs = {self.lookup_field: self.kwargs[self.lookup_url_kwarg]}

        self.validate_lookup_field_values()

        if self.instance is None:
            self.instance = get_instance_or_http404(self.model, **self.lookup_kwargs)

        return self.instance

    def validate_and_update(self):
        """
        Update all fields passed in from json.

        Step 1: Validate
        Step 2: Update
        """
        instance = self.get_instance()
        fields = self.bundle.keys()

        for field in fields:
            self.validate_bundle(field)
            setattr(instance, field, self.bundle[field])

        instance.save()
        instance.refresh_from_db()


class DetailUpdateAPI(DetailAPI):
    def patch(self, request, *args, **kwargs):
        self.validate_and_update()
        return self.get(request)
