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
    HTTP_EXCEPTIONS,
    AuthenticationError,
    PermissionsError,
    SerializerError,
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
            msg = f"{self.codepath} did not pass an object to "
            msg += "render_to_response, nor did its serializer method"
            raise ImproperlyConfigured(msg)

        return render_response(self.request, data, status_code)


class AbstractBaseAPI(SerializeModels, ValidateFields, APIResponse):
    model = None
    permissions = []
    payload_key = None

    def __init__(self, *args, **kwargs):
        self.codepath = f"{self.__module__}.{self.__class__.__name__}"

        if self.model is None:  # pragma: no cover
            raise ImproperlyConfigured(f"Model is not set on {self.codepath}")

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
        method = request.method.lower()
        handler = self.http_method_not_allowed

        if method in self.http_method_names:
            handler = getattr(self, method, self.http_method_not_allowed)

        try:
            self.check_permissions()
            self.set_bundle_from_request(request)
            return handler(request, *args, **kwargs)
        except HTTP_EXCEPTIONS as e:
            message = e.message
            status = e.status
        except AuthenticationError as e:
            message = e.message
            status = 401
        except ObjectDoesNotExist as e:
            if self.model and not isinstance(e, self.model.DoesNotExist):
                raise e
            message = "Not Found"
            status = 404
        except RequestDataTooBig:
            self.request._body = self.request.read(None)  # prevent further raises
            message = f"Max upload size is {filesizeformat(settings.DATA_UPLOAD_MAX_MEMORY_SIZE)}"
            status = 422
        except SerializerError as e:
            message = e.message
            status = 400
        except ValidationError as e:
            message = e.message
            status = 422

        return self.render_to_response(dict(message=message), status)

    def check_permissions(self):
        for perm in self.permissions:
            try:
                perm()(self.request, **self.kwargs)
            except HTTP_EXCEPTIONS as e:
                if settings.WORF_DEBUG:
                    raise PermissionsError(
                        f"Permission check {perm.__module__}.{perm.__name__} raised {e.__class__.__name__}. "
                        f"You'd normally see a {e.status} here but WORF_DEBUG=True."
                    ) from e
                raise e

    def get_instance(self):
        return self.instance if hasattr(self, "instance") else None

    def get_related_model(self, field):
        return self.model._meta.get_field(field).related_model

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
