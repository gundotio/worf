from datetime import datetime
from uuid import UUID

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import models
from django.utils.dateparse import parse_datetime

from worf.conf import settings
from worf.exceptions import NotImplementedInWorfYet


class ValidationMixin:
    boolean_values = {
        "1": True,
        "0": False,
        "true": True,
        "false": False,
    }

    secure_fields = [
        "password",
        "password_confirmation",
    ]

    def _coerce_bool(self, value):
        if isinstance(value, bool):
            return value

        return self.boolean_values.get(str(value).lower().strip(), None)

    def _validate_boolean(self, key):
        value = self.bundle[key]
        coerced = self._coerce_bool(value)

        if not isinstance(coerced, bool):
            raise ValidationError(
                f"Field {self.keymap[key]} accepts a boolean, got {value}, coerced to {coerced}"
            )

        return coerced

    def _validate_date(self, key):
        value = self.bundle[key]

        if not isinstance(value, str):
            return None

        return datetime.strptime(value, "%Y-%m-%d")

    def _validate_datetime(self, key):
        value = self.bundle[key]
        coerced = None

        if isinstance(value, str):
            coerced = parse_datetime(value)

        if not isinstance(coerced, datetime):
            raise ValidationError(
                f"Field {self.keymap[key]} accepts a iso datetime string, got {value}, coerced to {coerced}"
            )

        return coerced

    def _validate_many_to_many(self, key):
        value = self.bundle[key]

        if not isinstance(value, list):
            raise ValidationError(
                f"Field {self.keymap[key]} accepts an array, got {type(value)} {value}"
            )

    def _validate_string(self, key, max_length):
        value = self.bundle[key]

        if not isinstance(value, str):
            raise ValidationError(f"Field {self.keymap[key]} accepts string")

        if max_length is not None and len(value) > max_length:
            raise ValidationError(
                f"Field {self.keymap[key]} accepts a maximum of {max_length} characters"
            )

        return value

    def _validate_int(self, key):
        value = self.bundle[key]

        if value is None or value == "":
            return None

        try:
            integer = int(value)
        except (TypeError, ValueError):
            raise ValidationError(f"Field {self.keymap[key]} accepts an integer")

        return integer

    def _validate_positive_int(self, key):
        integer = self._validate_int(key)

        if integer < 0:
            raise ValidationError(
                f"Field {self.keymap[key]} accepts a positive integer"
            )

        return integer

    ############################################################################
    # Public methods for use downstream
    def coerce_array_of_integers(self, key):
        try:
            self.bundle[key] = [int(id) for id in self.bundle[key]]
        except ValueError:
            message = f"Field {self.keymap[key]} accepts an array of integers. Got {self.bundle[key]} instead."
            raise ValidationError(message + " I couldn't coerce the values.")

    def validate_int(self, value):
        if not isinstance(value, int):
            raise ValidationError(f"Expected integer, got {value}")

    def validate_numeric(self, value):
        try:
            int(value)
        except ValueError:
            raise ValidationError(f"Expected numeric, got {value}")

    def validate_uuid(self, value):
        try:
            assert value is not None
            return UUID(str(value))
        except (AssertionError, TypeError, ValueError):
            raise ValidationError(f"Expected UUID, got {value}")

    def validate_email(self, value):
        if not isinstance(value, str):
            raise ValidationError(f"{value} is not a valid email address")

        email = value.strip().lower()
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError(f"{value} is not a valid email address")
        return email

    def validate_bundle(self, key):
        """
        Handle basic type validation and coercion.

        @param key: the model attribute to check against.

        @raise NotImplementedInWorfYet: If the field type is not currently supported
        @raise ValidationError: If this is a write and `key` is not serializer editable
        @raise ValidationError: If a value fails to pass validation

        @return: If all checks pass, True is returned.

        Side Effects:
        As various bundle objects are parsed and validated, we reset the bundle.
        This may result in self.bundle changes.

        We expect to set a fully validated bundle keys and values.
        """
        serializer = self.get_serializer()
        write_methods = ("PATCH", "POST", "PUT")

        if self.request.method in write_methods and key not in serializer.write():
            message = f"{self.keymap[key]} is not editable"
            if settings.WORF_DEBUG:
                message += f":: {serializer}"
            raise ValidationError(message)

        annotation = (
            self.get_queryset().query.annotations.get(key)
            if hasattr(self, "get_queryset")
            else None
        )

        if not hasattr(self.model, key) and not annotation:
            raise ValidationError(f"{self.keymap[key]} does not exist")

        if key not in self.secure_fields and isinstance(self.bundle[key], str):
            self.bundle[key] = self.bundle[key].strip()

        field = (
            annotation.output_field if annotation else self.model._meta.get_field(key)
        )

        if field.blank and field.empty_strings_allowed and self.bundle[key] == "":
            pass

        elif field.null and self.bundle[key] is None:
            pass

        elif hasattr(self, f"validate_{key}"):
            self.bundle[key] = getattr(self, f"validate_{key}")(self.bundle[key])

        elif isinstance(field, models.UUIDField):
            self.bundle[key] = self.validate_uuid(self.bundle[key])

        elif isinstance(field, (models.CharField, models.TextField, models.SlugField)):
            self.bundle[key] = self._validate_string(key, field.max_length)

        elif isinstance(field, models.EmailField):
            self.bundle[key] = self.validate_email(self.bundle[key])

        elif isinstance(field, (models.IntegerField, models.SmallIntegerField)):
            # TODO check size of SmallIntegerField
            self.bundle[key] = self._validate_int(key)

        elif isinstance(field, models.PositiveIntegerField):
            self.bundle[key] = self._validate_positive_int(key)

        elif isinstance(field, models.ManyToManyField):
            self._validate_many_to_many(key)

        elif isinstance(field, models.BooleanField):
            self.bundle[key] = self._validate_boolean(key)

        elif isinstance(field, models.FileField):
            pass  # Django will raise an exception if handled improperly

        elif isinstance(field, models.ForeignKey):
            pass  # Django will raise an exception if handled improperly

        elif isinstance(field, models.DateTimeField):
            self.bundle[key] = self._validate_datetime(key)

        elif isinstance(field, models.DateField):
            self.bundle[key] = self._validate_date(key)

        elif isinstance(field, models.JSONField):
            pass
            # TODO check the type of json object we're expecting
            # try:
            #     json.loads(self.bundle[key])
            # except ValueError:
            #     raise ValidationError(f"Field {self.keymap[key]} requires valid JSON")

        else:
            message = f"{field.get_internal_type()} has no validation method for {key}"
            if settings.WORF_DEBUG:
                message += f":: Received {self.bundle[key]}"
            raise NotImplementedInWorfYet(message)
            # TODO
            # FileField
            # UUIDField
            # We don't handle 1:1 or FKs.

        return True
