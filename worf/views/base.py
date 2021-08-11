import json
import types
import warnings

from urllib.parse import parse_qs

from django.conf import settings
from django.core.exceptions import (
    ImproperlyConfigured,
    ObjectDoesNotExist,
    ValidationError,
)
from django.db import models
from django.http import JsonResponse
from django.middleware.gzip import GZipMiddleware
from django.views import View
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

from worf.casing import camel_to_snake, whitespace_to_camel
from worf.exceptions import HTTP_EXCEPTIONS, HTTP404, HTTP422, PermissionsException
from worf.serializers import LegacySerializer
from worf.validators import ValidationMixin

gzip_middleware = GZipMiddleware()


@method_decorator(never_cache, name="dispatch")
class APIResponse(View):
    def __init__(self, *args, **kwargs):
        self.codepath = f"{self.__module__}.{self.__class__.__name__}"
        return super().__init__(*args, **kwargs)

    def serialize(self):
        raise NotImplementedError

    def render_to_response(self, data=None, status_code=None):
        payload = data if data is not None else self.serialize()

        if payload is None:
            msg = f"{self.codepath} did not pass an object to "
            msg += "render_to_response, nor did its serializer method"
            raise ImproperlyConfigured(msg)

        response = JsonResponse(payload)
        # except TypeError:
        # TODO add something meaningful to the stack trace

        if status_code is not None:  # needs tests
            response.status_code = status_code

        return gzip_middleware.process_response(self.request, response)


class AbstractBaseAPI(APIResponse, ValidationMixin):
    model = None
    permissions = []
    api_method = "api"
    serializer = None
    payload_key = None

    def __init__(self, *args, **kwargs):
        self.codepath = f"{self.__module__}.{self.__class__.__name__}"

        if self.model is None:
            raise ImproperlyConfigured(f"Model is not set on {self.codepath}")

        if not isinstance(self.permissions, list):
            raise ImproperlyConfigured(
                f"{self.codepath}.permissions must be type: list"
            )

        for method in ["post", "patch", "put", "delete"]:
            if method in dir(self) and not len(self.permissions):
                warnings.warn(
                    "\n{} method allowed on {} without permissions.".format(
                        method.upper(),
                        self.codepath,
                    ),
                )

        for method in self.permissions:
            # append authorization functions to this class
            setattr(self, method.__name__, types.MethodType(method, self))

        super().__init__(*args, **kwargs)

    @property
    def name(self):
        if isinstance(self.payload_key, str):
            return self.payload_key
        return whitespace_to_camel(self.model._meta.verbose_name_plural)

    def _check_permissions(self):
        """Return a permissions exception when in debug mode instead of 404."""
        for method in self.permissions:
            permission_func = getattr(self, method.__name__)
            response = permission_func(self.request)
            if response == 200:
                continue

            if settings.DEBUG:
                raise PermissionsException(
                    "Permissions function {}.{} returned {}. You'd normally see a 404 here but DEBUG=True.".format(
                        method.__module__, method.__name__, response
                    )
                )

            try:
                raise response
            except TypeError:
                raise ImproperlyConfigured(
                    "Permissions function {}.{} must return 200 or an HTTPException".format(
                        method.__module__, method.__name__
                    )
                )

    def _assemble_bundle_from_request_body(self):

        if self.request.content_type == "multipart/form-data":
            # Avoid RawPostDataException
            # TODO investigate why test did not catch this error
            raw_bundle = {}

        elif self.request.body:  # and self.request.body != b'--BoUnDaRyStRiNg--\r\n':
            try:
                raw_bundle = json.loads(self.request.body)
            except json.decoder.JSONDecodeError:
                # print("\n\n~~~~~~~~~~~~~~~~~~~~~~", self.request.body, '\n\n')
                raw_bundle = {}
        else:
            raw_bundle = {}

        self.set_bundle(raw_bundle)

    def _get_lookup_field(self, field):
        related = field.find("__")

        """Support one level of related field reference."""
        if related != -1:
            related_field = field[:related]
            target_field = field[related + 2 :]

            if target_field in ["gt", "lt", "contains", "startswith", "gte", "lte"]:
                return False

            if target_field.find("__") != -1:
                return False

            return self.get_related_model(related_field)._meta.get_field(target_field)
            # TODO if there is another reference, recurse

        return self.model._meta.get_field(field)

    def get_related_model(self, field):
        return self.model._meta.get_field(field).related_model

    def get_serializer(self):
        if self.serializer:
            return self.serializer()
        if self.api_method:
            return LegacySerializer(self.model, self.api_method)
        msg = f"{self.__name__}.get_serializer() did not return a serializer"
        raise ImproperlyConfigured(msg)

    def validate_lookup_field_values(self):
        # todo check for each lookup kwarg
        for field, url_kwarg in self.lookup_kwargs.items():
            lookup_field = self._get_lookup_field(field)

            if isinstance(lookup_field, models.UUIDField):
                self.validate_uuid(url_kwarg)
            elif isinstance(
                lookup_field,
                (
                    models.ForeignKey,
                    models.IntegerField,
                    models.PositiveIntegerField,
                    models.SmallIntegerField,
                ),
            ):
                self.validate_numeric(url_kwarg)

    def set_bundle_from_querystring(self):
        # parse_qs gives us a dictionary where all values are lists
        qs = parse_qs(self.request.META["QUERY_STRING"])

        # TODO: TLDR; Switch to POST for search instead of GET/querystring params.
        # we want to preserve strings wherever there are not duplicate keys
        # Step through the list and construct a dictionary for all fields
        # that are not duplicated

        # fundamentally all urlparams are treated as arrays natively.
        # we can't enforce type coersion here...

        # we can't assume everything is an array or everything is not an array
        # when it's a querystring

        raw_bundle = {}
        for key, value in qs.items():
            raw_bundle[key] = value[0] if len(value) == 1 else value

        self.set_bundle(raw_bundle)

    def set_bundle(self, raw):
        self.bundle = {}
        if not raw:
            return  # No need to loop or set self.bundle again if it's empty

        for key in raw.keys():
            field = camel_to_snake(key)
            self.bundle[field] = raw[key]

    def dispatch(self, request, *args, **kwargs):
        method = request.method.lower()
        handler = self.http_method_not_allowed

        if method in self.http_method_names:
            handler = getattr(self, method, self.http_method_not_allowed)

        try:
            self._check_permissions()  # only returns 200 or HTTP_EXCEPTIONS
            self._assemble_bundle_from_request_body()  # sets self.bundle
            return handler(request, *args, **kwargs)  # calls self.serialize()
        except HTTP_EXCEPTIONS as e:
            return self.render_to_response(dict(message=e.message), e.status)
        except ObjectDoesNotExist:
            return self.render_to_response(
                dict(message=HTTP404.message), HTTP404.status
            )
        except ValidationError as e:
            return self.render_to_response(dict(message=e.message), HTTP422.status)
