from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import models
from django.db.utils import IntegrityError

from worf.casing import snake_to_camel
from worf.shortcuts import get_instance_or_http404
from worf.views.base import AbstractBaseAPI


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

    def set_foreign_key(self, instance, key):
        related_model = self.get_related_model(key)
        try:
            related_instance = related_model.objects.get(pk=self.bundle[key])
        except related_model.DoesNotExist as e:
            raise ValidationError(f"Invalid {snake_to_camel(key)}") from e
        setattr(instance, key, related_instance)

    def set_many_to_many(self, instance, key):
        try:
            getattr(instance, key).set(self.bundle[key])
        except IntegrityError as e:
            raise ValidationError(f"Invalid {snake_to_camel(key)}") from e

    def validate_and_update(self):
        """
        Update all fields passed in from json.

        Step 1: Validate
        Step 2: Update
        """
        instance = self.get_instance()
        keys = self.bundle.keys()

        for key in keys:
            self.validate_bundle(key)

            field = self.model._meta.get_field(key)

            if isinstance(field, models.ForeignKey):
                self.set_foreign_key(instance, key)
                continue

            if isinstance(field, models.ManyToManyField):
                self.set_many_to_many(instance, key)
                continue

            setattr(instance, key, self.bundle[key])

        instance.save()
        instance.refresh_from_db()


class DetailUpdateAPI(DetailAPI):
    def patch(self, request, *args, **kwargs):
        self.validate_and_update()
        return self.get(request)
