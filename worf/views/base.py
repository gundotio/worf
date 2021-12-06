import json
import types
import warnings

from io import BytesIO
from urllib.parse import parse_qs

from django.conf import settings
from django.core.exceptions import (
    ImproperlyConfigured,
    ObjectDoesNotExist,
    ValidationError,
)
from django.db import models
from django.http import HttpResponse, JsonResponse
from django.template.response import TemplateResponse
from django.views import View
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

from worf.casing import camel_to_snake, snake_to_camel
from worf.exceptions import HTTP_EXCEPTIONS, HTTP404, HTTP422, PermissionsException
from worf.serializers import LegacySerializer
from worf.validators import ValidationMixin

api_name = getattr(settings, "WORF_API_NAME", "Worf API")
api_root = getattr(settings, "WORF_API_ROOT", "/api/")


@method_decorator(never_cache, name="dispatch")
class APIResponse(View):
    def __init__(self, *args, **kwargs):
        self.codepath = f"{self.__module__}.{self.__class__.__name__}"
        return super().__init__(*args, **kwargs)

    def serialize(self):
        raise NotImplementedError

    def render_to_response(self, data=None, status_code=200):
        if data is None:
            data = self.serialize()

        if data is None:
            msg = f"{self.codepath} did not pass an object to "
            msg += "render_to_response, nor did its serializer method"
            raise ImproperlyConfigured(msg)

        is_html_request = (
            "text/html" in self.request.headers.get("Accept", "")
            and self.request.GET.get("format") != "json"
        )

        json_kwargs = dict(json_dumps_params=dict(indent=2)) if is_html_request else {}

        response = JsonResponse(data, **json_kwargs) if data != "" else HttpResponse()
        response.status_code = status_code

        if is_html_request:
            template = "worf/api.html"
            context = dict(
                api_name=api_name,
                api_root=api_root,
                content=response.content.decode("utf-8"),
                response=response,
            )
            response = TemplateResponse(self.request, template, context=context)
            response.status_code = status_code
            response.render()

        return response


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
        verbose_name_plural = self.model._meta.verbose_name_plural
        return snake_to_camel(verbose_name_plural.replace(" ", "_").lower())

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
        msg = f"{type(self).__name__}.get_serializer() did not return a serializer"
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

    def flatten_bundle(self, raw_bundle):
        # parse_qs gives us a dictionary where all values are lists
        return {
            key: value[0] if len(value) == 1 else value
            for key, value in raw_bundle.items()
        }

    def get_parts(self, request):
        if request.method == "POST":
            return request.POST, request.FILES

        return request.parse_file_upload(request.META, BytesIO(request.body))

    def set_bundle(self, raw_bundle):
        self.bundle = {}
        self.keymap = {}

        if not raw_bundle:
            return

        for key in raw_bundle.keys():
            field = camel_to_snake(key)
            self.bundle[field] = raw_bundle[key]
            self.keymap[field] = key

    def set_bundle_from_query_string(self, request):
        raw_bundle = self.flatten_bundle(parse_qs(request.META["QUERY_STRING"]))

        self.set_bundle(raw_bundle)

    def set_bundle_from_request_body(self, request):
        raw_bundle = {}

        if request.content_type == "multipart/form-data":
            post, files = self.get_parts(request)
            raw_bundle.update(self.flatten_bundle(post))
            raw_bundle.update(self.flatten_bundle(files))
        elif request.body:
            try:
                raw_bundle = json.loads(request.body)
            except json.decoder.JSONDecodeError:
                pass

        self.set_bundle(raw_bundle)

    def dispatch(self, request, *args, **kwargs):
        method = request.method.lower()
        handler = self.http_method_not_allowed

        if method in self.http_method_names:
            handler = getattr(self, method, self.http_method_not_allowed)

        try:
            self._check_permissions()  # only returns 200 or HTTP_EXCEPTIONS
            self.set_bundle_from_request_body(request)
            return handler(request, *args, **kwargs)  # calls self.serialize()
        except HTTP_EXCEPTIONS as e:
            return self.render_to_response(dict(message=e.message), e.status)
        except ObjectDoesNotExist:
            return self.render_to_response(
                dict(message=HTTP404.message), HTTP404.status
            )
        except ValidationError as e:
            return self.render_to_response(dict(message=e.message), HTTP422.status)
