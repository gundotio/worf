from django.core.exceptions import ValidationError
from django.db import models
from django.db.utils import IntegrityError


class AssignAttributes:
    def save(self, instance, bundle):
        items = [
            (key, getattr(self.model, key), value) for key, value in bundle.items()
        ]

        for key, attr, value in items:
            if isinstance(value, models.Model):
                setattr(instance, key, value)
                continue

            if isinstance(attr.field, models.ForeignKey):
                self.set_foreign_key(instance, key, value)
                continue

            if isinstance(attr.field, models.ManyToManyField):
                continue

            setattr(instance, key, value)

        instance.save()

        for key, attr, value in items:
            if isinstance(attr.field, models.ManyToManyField):
                if not attr.through._meta.auto_created:
                    self.set_many_to_many_with_through(instance, key, value)
                    continue

                self.set_many_to_many(instance, key, value)

    def set_foreign_key(self, instance, key, value):
        related_model = self.get_related_model(key)
        try:
            related_instance = (
                related_model.objects.get(pk=value) if value is not None else None
            )
        except related_model.DoesNotExist as e:
            raise ValidationError(f"Invalid {self.keymap[key]}") from e
        setattr(instance, key, related_instance)

    def set_many_to_many(self, instance, key, value):
        try:
            getattr(instance, key).set(value)
        except (IntegrityError, ValueError) as e:
            raise ValidationError(f"Invalid {self.keymap[key]}") from e

    def set_many_to_many_with_through(self, instance, key, value):
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
                            item_key: item_value
                            for item_key, item_value in item.items()
                            if item_key != target_field_name
                        },
                        **{
                            model_name: instance,
                            reverse_name: item[target_field_name],
                        },
                    )
                    for item in value
                ]
            )
        except (AttributeError, IntegrityError, ValueError) as e:
            raise ValidationError(f"Invalid {self.keymap[key]}") from e

    def validate(self):
        for key in self.bundle.keys():
            self.validate_bundle(key)

            field = self.model._meta.get_field(key)

            if self.bundle[key] is None and not field.null:
                raise ValidationError(f"Invalid {self.keymap[key]}")
