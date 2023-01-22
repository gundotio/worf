import json
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
from worf.exceptions import (
    ActionError,
    AuthenticationError,
    DataConflict,
    FieldError,
    NotFound,
    WorfError,
)
from worf.renderers import render_response
from worf.serializers import SerializeModels
from worf.validators import ValidateFields


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
            message = f"{self.codepath} did not pass an object to "
            message += "render_to_response, nor did its serializer method"
            raise ImproperlyConfigured(message)

        return render_response(self.request, data, status_code, self)


class AbstractBaseAPI(SerializeModels, ValidateFields, APIResponse):
    model = None
    permissions = []
    payload_key = None

    def __init__(self, *args, **kwargs):
        self.codepath = f"{self.__module__}.{self.__class__.__name__}"

        if not isinstance(self.permissions, list):  # pragma: no cover
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

        super().__init__(*args, **kwargs)

    @property
    def name(self):
        if isinstance(self.payload_key, str):
            return self.payload_key
        verbose_name_plural = self.model._meta.verbose_name_plural
        return snake_to_camel(verbose_name_plural.replace(" ", "_").lower())

    def dispatch(self, request, *args, **kwargs):
        try:
            response = self.perform_dispatch(request, *args, **kwargs)
        except ActionError as e:
            response = self.render_error(e.message, 400)
        except AuthenticationError as e:
            response = self.render_error(e.message, 401)
        except DataConflict as e:
            response = self.render_error(e.message, 409)
        except FieldError as e:
            response = self.render_error(e.message, 400)
        except NotFound as e:
            response = self.render_error(e.message, 404)
        except ValidationError as e:
            response = self.render_error(e.message, 422)
        return response

    def perform_dispatch(self, request, *args, **kwargs):
        try:
            handler = self.get_handler(request, *args, **kwargs)
            self.check_permissions()
            self.set_bundle_from_request(request)
            response = handler(request, *args, **kwargs)
        except ObjectDoesNotExist as e:
            if self.model and not isinstance(e, self.model.DoesNotExist):
                raise e
            raise NotFound from e
        except RequestDataTooBig as e:
            self.request._body = self.request.read(None)  # prevent further raises
            max_upload_size = filesizeformat(settings.DATA_UPLOAD_MAX_MEMORY_SIZE)
            raise ValidationError(f"Max upload size is {max_upload_size}") from e
        return response

    def render_error(self, message, status):
        return self.render_to_response(dict(message=message), status)

    def check_permissions(self):
        try:
            for perm in self.permissions:
                perm()(self.request, **self.kwargs)
        except WorfError as e:
            if settings.WORF_DEBUG:  # pragma: no cover
                check = f"{perm.__module__}.{perm.__name__}"
                error = e.__class__.__name__
                raise type(e)(f"{e.message}: Permission {check} raised {error}") from e
            raise e

    def get_handler(self, request, *args, **kwargs):
        method = request.method.lower()
        handler = self.http_method_not_allowed
        if method in self.http_method_names:
            handler = getattr(self, method, self.http_method_not_allowed)
        return handler

    def get_instance(self):
        return self.instance if hasattr(self, "instance") else None

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
