import re
from datetime import datetime
from uuid import UUID

from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.dateparse import parse_datetime
from django.utils.html import strip_tags

from worf.exceptions import NotImplementedInWorfYet
from worf.casing import clean_lookup_keywords, snake_to_camel


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
                f"Field {snake_to_camel(key)} accepts a boolean, got {value}, coerced to {coerced}"
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
                f"Field {snake_to_camel(key)} accepts a iso datetime string, got {value}, coerced to {coerced}"
            )

        return coerced

    def _validate_many_to_many(self, key):
        value = self.bundle[key]

        if not isinstance(value, list):
            raise ValidationError(
                f"Field {snake_to_camel(key)} accepts an array, got {type(value)} {value}"
            )

        self.coerce_array_of_integers(key)

    def _validate_string(self, key, max_length):
        value = self.bundle[key]

        if not isinstance(value, str):
            raise ValidationError(f"Field {snake_to_camel(key)} accepts string")

        if key not in self.secure_fields:
            value = strip_tags(value).strip()

        if max_length is not None and len(value) > max_length:
            raise ValidationError(
                f"Field {snake_to_camel(key)} accepts a maximum of {max_length} characters"
            )

        return value

    def _validate_int(self, key):
        value = self.bundle[key]

        if value is None or value == "":
            return None

        try:
            integer = int(value)
        except (TypeError, ValueError):
            raise ValidationError(f"Field {snake_to_camel(key)} accepts an integer")

        return integer

    def _validate_positive_int(self, key):
        integer = self._validate_int(key)

        if integer < 0:
            raise ValidationError(
                f"Field {snake_to_camel(key)} accepts a positive integer"
            )

        return integer

    ############################################################################
    # Public methods for use downstream
    def coerce_array_of_integers(self, key):
        try:
            self.bundle[key] = [int(id) for id in self.bundle[key]]
        except ValueError:
            message = f"Field {snake_to_camel(key)} accepts an array of integers. Got {self.bundle[key]} instead."
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
        if value is None:
            raise ValidationError(f"Expected UUID, got {value}")
        try:
            return UUID(str(value))
        except (TypeError, ValueError):
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

        @param key _str_ the model attribute to check against.
        @return value:
            - If the HTTP method is not PATCH and `key` does not exist in the
        model serializer method, return False.
            - If an error is detected, ValidationError will be raised
            - If all checks pass, True is returned

        Side Effects:
        As various bundle objects are parsed and validated, we reset the bundle.
        This may result in self.bundle changes.

        We expect to set a fully validated bundle keys and values.
        """
        # POST cannot validate b/c it allows fields not in api_update_fields
        # self.request.method == 'POST' or
        clean_key = clean_lookup_keywords(key)
        serializer = self.get_serializer()
        if self.request.method in ("PATCH", "PUT") and key not in serializer.write():
            message = f"{snake_to_camel(key)} is not editable"
            if settings.DEBUG:
                message += f":: {serializer}"
            raise ValidationError(message)

        if not hasattr(self.model, clean_key):
            raise ValidationError(f"{snake_to_camel(clean_key)} does not exist")

        field = self.model._meta.get_field(clean_key)

        if hasattr(self, f"validate_{clean_key}"):
            self.bundle[key] = getattr(self, f"validate_{clean_key}")(self.bundle[key])

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
            #     raise ValidationError(f"Field {snake_to_camel(key)} requires valid JSON")

        else:
            message = f"{field.get_internal_type()} has no validation method for {key}"
            if settings.DEBUG:
                message += f":: Received {self.bundle[key]}"
            raise NotImplementedInWorfYet(message)
            # TODO
            # FileField
            # UUIDField
            # We don't handle 1:1 or FKs.

        return True
