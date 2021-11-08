from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import models
from django.db.utils import IntegrityError

from worf.casing import snake_to_camel
from worf.views.base import AbstractBaseAPI


class DetailAPI(AbstractBaseAPI):
    lookup_field = "id"
    lookup_url_kwarg = "id"
    queryset = None

    def get(self, request, *args, **kwargs):
        return self.render_to_response()

    def serialize(self):
        """Return the model api, used for responses."""
        serializer = self.get_serializer()
        payload = serializer.read(self.get_instance())
        if not isinstance(payload, dict):
            raise ImproperlyConfigured(f"{serializer} did not return a dictionary")
        return payload

    def get_queryset(self):
        if self.queryset is None:
            return self.model.objects.all()
        return self.queryset.all()

    def get_instance(self):
        self.lookup_kwargs = {self.lookup_field: self.kwargs[self.lookup_url_kwarg]}

        self.validate_lookup_field_values()

        if not hasattr(self, "instance"):
            self.instance = self.get_queryset().get(**self.lookup_kwargs)

        return self.instance

    def set_foreign_key(self, instance, key):
        related_model = self.get_related_model(key)
        try:
            related_instance = (
                related_model.objects.get(pk=self.bundle[key])
                if self.bundle[key] is not None
                else None
            )
        except related_model.DoesNotExist as e:
            raise ValidationError(f"Invalid {snake_to_camel(key)}") from e
        setattr(instance, key, related_instance)

    def set_many_to_many(self, instance, key):
        try:
            getattr(instance, key).set(self.bundle[key])
        except (IntegrityError, ValueError) as e:
            raise ValidationError(f"Invalid {snake_to_camel(key)}") from e

    def set_many_to_many_with_through(self, instance, key):
        try:
            attr = getattr(self.model, key)

            through_model = attr.through
            model_name = self.model._meta.model_name
            target_field_name = attr.field.m2m_target_field_name()
            reverse_name = attr.field.m2m_reverse_name()

            getattr(instance, key).clear()

            through_model.objects.bulk_create(
                [
                    through_model(
                        **{
                            key: value
                            for key, value in item.items()
                            if key != target_field_name
                        },
                        **{
                            model_name: instance,
                            reverse_name: item[target_field_name],
                        },
                    )
                    for item in self.bundle[key]
                ]
            )
        except (AttributeError, IntegrityError, ValueError) as e:
            raise ValidationError(f"Invalid {snake_to_camel(key)}") from e

    def update(self):
        instance = self.get_instance()

        self.validate()

        for key in self.bundle.keys():
            attr = getattr(self.model, key)

            if isinstance(attr.field, models.ForeignKey):
                self.set_foreign_key(instance, key)
                continue

            if isinstance(attr.field, models.ManyToManyField):
                if not attr.through._meta.auto_created:
                    self.set_many_to_many_with_through(instance, key)
                    continue

                self.set_many_to_many(instance, key)
                continue

            setattr(instance, key, self.bundle[key])

        instance.save()
        instance.refresh_from_db()

        return instance

    def validate(self):
        for key in self.bundle.keys():
            self.validate_bundle(key)

            field = self.model._meta.get_field(key)

            if self.bundle[key] is None and not field.null:
                raise ValidationError(f"Invalid {snake_to_camel(key)}")


class DetailUpdateAPI(DetailAPI):
    def patch(self, request, *args, **kwargs):
        self.update()
        return self.get(request)
