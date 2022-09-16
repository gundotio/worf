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
                has_through = not attr.through._meta.auto_created

                if has_through and any(isinstance(item, dict) for item in value):
                    self.set_many_to_many_with_through(instance, key, value)
                    continue

                self.set_many_to_many(instance, key, value)

    def resolve_relation(self, key, value):
        related_model = getattr(self.model, key).field.related_model
        lookup_field = getattr(getattr(related_model, "Api", ""), "lookup_field", "pk")
        try:
            value = related_model.objects.get(**{lookup_field: value})
        except related_model.DoesNotExist as e:
            raise ValueError from e
        return value

    def set_foreign_key(self, instance, key, value):
        try:
            value = self.resolve_relation(key, value) if value is not None else None
        except ValueError as e:
            raise ValidationError(f"Invalid {self.keymap[key]}") from e
        setattr(instance, key, value)

    def set_many_to_many(self, instance, key, value):
        related_manager = getattr(instance, key)
        related_model = related_manager.model
        lookup_field = getattr(getattr(related_model, "Api", ""), "lookup_field", "pk")
        try:
            if lookup_field != "pk":
                items = related_model.objects.filter(**{f"{lookup_field}__in": value})
                assert len(items) == len(value)
                value = items
            related_manager.set(value)
        except (AssertionError, IntegrityError, ValueError) as e:
            raise ValidationError(f"Invalid {self.keymap[key]}") from e

    def set_many_to_many_with_through(self, instance, key, value):
        try:
            attr = getattr(self.model, key)
            through_model = attr.through
            model_name = self.model._meta.model_name
            target_key = attr.field.m2m_target_field_name()
            relation_name = attr.field.m2m_reverse_field_name()

            getattr(instance, key).clear()

            through_model.objects.bulk_create(
                [
                    through_model(
                        **{
                            item_key: item_value
                            for item_key, item_value in item.items()
                            if item_key != target_key
                        },
                        **{
                            model_name: instance,
                            relation_name: self.resolve_relation(key, item[target_key]),
                        },
                    )
                    for item in value
                ]
            )
        except (AttributeError, IntegrityError, ValueError) as e:
            raise ValidationError(f"Invalid {self.keymap[key]}") from e

    def validate(self):
        instance = self.get_instance()

        for key in self.bundle.keys():
            self.validate_bundle(key)

            field = self.model._meta.get_field(key)

            if self.bundle[key] is None and not field.null:
                raise ValidationError(f"Invalid {self.keymap[key]}")

            if field.unique:
                other_records = self.model.objects.exclude(pk=instance.pk)

                if other_records.filter(**{key: self.bundle[key]}).exists():
                    raise ValidationError(f"Field {self.keymap[key]} must be unique")
