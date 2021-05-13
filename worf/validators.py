from datetime import datetime
from uuid import UUID

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.html import strip_tags

from worf.exceptions import HTTP400, NotImplementedInWorfYet
from worf.casing import snake_to_camel


class ValidationMixin:
    def _coerce_bool(self, value):
        return {
            "1": True,
            "0": False,
            "true": True,
            "false": False,
            True: True,
            False: False,
        }.get(str(value).lower().strip(), None)

    def _validate_bundle_bool(self, key):
        coerced = self._coerce_bool(self.bundle[key])
        if not isinstance(coerced, bool):
            msg = "Field {} accepts a boolean. Got {}, coerced to {}. Full bundle:\n\n{}".format(
                snake_to_camel(key),
                self.bundle[key],
                coerced,
                self.bundle,
            )
            raise HTTP400(msg)

        return coerced

    def _validate_bundle_date_or_none(self, key):
        if isinstance(self.bundle[key], str):
            return datetime.strptime(self.bundle[key], "%Y-%m-%d")

        return None

    def _validate_bundle_many_to_many(self, key):
        if not isinstance(self.bundle[key], list):
            msg = "Field {} accepts an array. Got {} {} instead.".format(
                snake_to_camel(key),
                type(self.bundle[key]),
                self.bundle[key],
            )
            raise HTTP400(msg)

        self.coerce_array_of_integers(key)

    def _validate_bundle_str(self, key, max_len):
        if not isinstance(self.bundle[key], str):
            raise ValidationError(f"Field {snake_to_camel(key)} accepts string")

        if max_len is not None and len(self.bundle[key]) > max_len:
            raise HTTP400(
                f"Field {snake_to_camel(key)} accepts a maximum of {max_len} characters"
            )

        return strip_tags(self.bundle[key])

    def _validate_bundle_int_or_none(self, key):
        if self.bundle[key] is None or self.bundle[key] == "null":
            return None

        try:
            integer = int(self.bundle[key])
        except (TypeError, ValueError):
            raise ValidationError(f"Field {snake_to_camel(key)} accepts an integer")

        return integer

    def _validate_bundle_positive_int(self, key):
        integer = self._validate_bundle_int_or_none(key)

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
            msg = f"Field {snake_to_camel(key)} accepts an array of integers. Got {self.bundle[key]} instead."
            raise ValidationError(msg + " I couldn't coerce the values.")

    def get_field_type(self, key):
        return self.model._meta.get_field(key).get_internal_type()

    def validate_int(self, value):
        if not isinstance(value, int):
            raise ValidationError(f"Expected integer, got {value}")

    def validate_uuid(self, value):
        if value is None:
            raise ValidationError(f"Expected UUID, got {value}")
        try:
            return UUID(value)
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
            - If an error is detected, HTTP400 or ValidationError will be raised
            - If all checks pass, True is returned

        Side Effects:
        As various bundle objects are parsed and validated, we reset the bundle.
        This may result in self.bundle changes.

        We expect to set a fully validated bundle keys and values.
        """
        # POST cannot validate b/c it allows fields not in api_update_fields
        # self.request.method == 'POST' or
        serializer = self.get_serializer()
        if self.request.method in ("PATCH", "PUT") and key not in serializer.write():
            err_msg = f"{snake_to_camel(key)} is not editable"
            if settings.DEBUG:
                err_msg += f":: {serializer}"
            raise ValidationError(err_msg)

        if not hasattr(self.model, key):
            raise ValidationError(f"{snake_to_camel(key)} does not exist")

        field_type = self.get_field_type(key)

        if hasattr(self, f"validate_{key}"):
            self.bundle[key] = getattr(self, f"validate_{key}")(self.bundle[key])

        elif field_type in ["CharField", "TextField", "SlugField"]:
            max_len = self.model._meta.get_field(key).max_length
            self.bundle[key] = self._validate_bundle_str(key, max_len)

        elif field_type == "EmailField":
            self.bundle[key] = self.validate_email(self.bundle[key])

        elif field_type in ["IntegerField", "SmallIntegerField"]:
            # TODO check size of SmallIntegerField
            self.bundle[key] = self._validate_bundle_int_or_none(key)

        elif field_type == "PositiveIntegerField":
            self.bundle[key] = self._validate_bundle_positive_int(key)

        elif field_type == "ManyToManyField":
            self._validate_bundle_many_to_many(key)

        elif field_type in ["BooleanField"]:
            self.bundle[key] = self._validate_bundle_bool(key)

        elif field_type in ["ForeignKey"]:
            pass  # Django will raise an exception if handled improperly

        elif field_type in ["DateField"]:
            self.bundle[key] = self._validate_bundle_date_or_none(key)

        elif field_type in ["JSONField"]:
            pass
            # TODO check the type of json object we're expecting
            # try:
            #     json.loads(self.bundle[key])
            # except ValueError:
            #     raise ValidationError(f"Field {snake_to_camel(key)} requires valid JSON")

        else:
            err_msg = f"{field_type} has no validation method for {key}"
            if settings.DEBUG:
                err_msg += f":: Received {self.bundle[key]}"
            raise NotImplementedInWorfYet(err_msg)
            # TODO
            # FileField
            # UUIDField
            # We don't handle 1:1 or FKs.

        return True
