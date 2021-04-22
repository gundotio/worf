from django.core.exceptions import ImproperlyConfigured

from worf.views.base import AbstractBaseAPI
from worf.shortcuts import get_instance_or_http404


class ChoicesFieldOptionsAPI(AbstractBaseAPI):
    def get(self, request, *args, **kwargs):
        return self.render_to_response()

    def serialize(self):
        return getattr(self.model, self.api_method)()


class DetailAPI(AbstractBaseAPI):
    lookup_field = "id"
    lookup_url_kwarg = "id"
    instance = None

    def get(self, request, *args, **kwargs):
        return self.render_to_response()

    @classmethod
    def api_update_field_method_name(cls):
        return f"{cls.api_method}_update_fields"

    def get_serializer(self):
        """Return the model api_update_fields, used for update."""
        if self.serializer is not None:
            return self.serializer.write()
        return getattr(self.get_instance(), self.api_update_field_method_name())()

    def serialize(self):
        """Return the model api, used for responses."""

        # Deprecate ------------------------------------------------------------
        if self.serializer is None:
            payload = getattr(self.get_instance(), self.api_method)()
            msg = "{}.{}() did not return a dictionary".format(
                self.model.__name__, self.api_method
            )
        # ------------------------------------------------------------ Deprecate
        else:
            payload = self.serializer(self.get_instance()).read()
            msg = "{} did not return a dictionary".format(self.serializer)

        if not isinstance(payload, dict):
            raise ImproperlyConfigured(msg)
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

        instance.save(update_fields=fields)
        instance.refresh_from_db()


class DetailUpdateAPI(DetailAPI):
    def patch(self, request, *args, **kwargs):
        self.validate_and_update()
        return self.get(request)
