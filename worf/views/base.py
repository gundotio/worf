import json
import types
import warnings
from io import BytesIO
from urllib.parse import parse_qs

from django.core.exceptions import (
    ImproperlyConfigured,
    ObjectDoesNotExist,
    RequestDataTooBig,
    ValidationError,
)
from django.template.defaultfilters import filesizeformat
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache

from worf.casing import camel_to_snake, snake_to_camel
from worf.conf import settings
from worf.exceptions import HTTP404, HTTP422, HTTP_EXCEPTIONS, PermissionsException
from worf.renderers import render_response
from worf.serializers import LegacySerializer
from worf.validators import ValidationMixin


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

        return render_response(self.request, data, status_code)


class AbstractBaseAPI(APIResponse, ValidationMixin):
    model = None
    permissions = []
    api_method = "api"
    serializer = None
    staff_serializer = None
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

            if settings.WORF_DEBUG:
                raise PermissionsException(
                    "Permissions function {}.{} returned {}. You'd normally see a 404 here but WORF_DEBUG=True.".format(
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

    def get_instance(self):
        return self.instance if hasattr(self, "instance") else None

    def get_related_model(self, field):
        return self.model._meta.get_field(field).related_model

    def get_serializer(self):
        context = dict(request=self.request, **self.get_serializer_context())
        if self.staff_serializer and self.request.user.is_staff:
            return self.staff_serializer(context=context)
        if self.serializer:
            return self.serializer(context=context)
        if self.api_method:
            return LegacySerializer(self.model, self.api_method)
        msg = f"{type(self).__name__}.get_serializer() did not return a serializer"
        raise ImproperlyConfigured(msg)

    def get_serializer_context(self):
        return {}

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

    def set_bundle(self, raw_bundle, allow_negations=False):
        self.bundle = {}
        self.keymap = {}

        if not raw_bundle:
            return

        for key in raw_bundle.keys():
            field = (
                camel_to_snake(key[:-1]) + "!"
                if allow_negations and key.endswith("!")
                else camel_to_snake(key)
            )
            self.bundle[field] = raw_bundle[key]
            self.keymap[field] = key

    def set_bundle_from_request(self, request):
        if request.method == "GET":
            self.set_bundle_from_query_string(request)
            return

        self.set_bundle_from_request_body(request)

    def set_bundle_from_query_string(self, request):
        raw_bundle = self.flatten_bundle(parse_qs(request.META["QUERY_STRING"]))

        strings = dict(true=True, false=False, null=None)

        coerced_bundle = {
            key: strings.get(str(value).lower(), value)
            for key, value in raw_bundle.items()
        }

        self.set_bundle(coerced_bundle, allow_negations=True)

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
            self.set_bundle_from_request(request)
            return handler(request, *args, **kwargs)  # calls self.serialize()
        except HTTP_EXCEPTIONS as e:
            return self.render_to_response(dict(message=e.message), e.status)
        except ObjectDoesNotExist as e:
            if self.model and not isinstance(e, self.model.DoesNotExist):
                raise e
            return self.render_to_response(
                dict(message=HTTP404.message), HTTP404.status
            )
        except RequestDataTooBig:
            self.request._body = self.request.read(None)  # prevent further raises
            message = f"Max upload size is {filesizeformat(settings.DATA_UPLOAD_MAX_MEMORY_SIZE)}"
            return self.render_to_response(dict(message=message), HTTP422.status)
        except ValidationError as e:
            return self.render_to_response(dict(message=e.message), HTTP422.status)
