import json
import types
import warnings

from urllib.parse import parse_qs

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.middleware.gzip import GZipMiddleware
from django.views import View
from django.views.decorators.cache import never_cache
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator

from api.core.casing import camel_to_snake, whitespace_to_camel
from api.core.exceptions import HTTP_EXCEPTIONS, PermissionsException, HTTP420
from api.core.validators import ValidationMixin

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
    payload_key = None

    def __init__(self, *args, **kwargs):
        self.codepath = f"{self.__module__}.{self.__class__.__name__}"

        if self.model is None:
            raise ImproperlyConfigured(f"Model is not set on {self.codepath}")

        if not isinstance(self.permissions, list):
            raise ImproperlyConfigured(
                f"{self.codepath}.permissions must be type: list"
            )

        for method in ["post", "patch", "delete"]:
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
        name = whitespace_to_camel(self.model._meta.verbose_name_plural)
        return name[:1].lower() + name[1:]

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

    def _get_lookup_field_type(self, field):

        related = field.find("__")
        """Support one level of related field reference."""
        if related != -1:
            model = field[:related]
            target = field[related + 2 :]

            if target in ["gt", "lt", "contains", "startswith", "gte", "lte"]:
                return False

            if target.find("__") != -1:
                return False

            return (
                self.model._meta.get_field(model)
                .related_model._meta.get_field(target)
                .get_internal_type()
            )
            # TODO if there is another reference, recurse

        return self.model._meta.get_field(field).get_internal_type()

    def validate_lookup_field_values(self):
        # todo check for each lookup kwarg
        for field, url_kwarg in self.lookup_kwargs.items():

            lookup_field_type = self._get_lookup_field_type(field)

            if lookup_field_type == "UUIDField":
                self.validate_uuid(url_kwarg)
            elif lookup_field_type in [
                "IntegerField",
                "SmallIntegerField",
                "PositiveIntergerField",
                "ForeignKey",
            ]:
                self.validate_int(url_kwarg)

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
        if request.method.lower() in self.http_method_names:
            handler = getattr(
                self, request.method.lower(), self.http_method_not_allowed
            )
        else:
            handler = self.http_method_not_allowed

        try:
            self._check_permissions()
            self._assemble_bundle_from_request_body()
            return handler(request, *args, **kwargs)
        except HTTP_EXCEPTIONS as e:
            message = e.message
            return self.render_to_response(dict(message=message), e.status)

    def get(self, request, *args, **kwargs):
        """Get is always implicitly available on every endpoint."""
        return self.render_to_response()


class ChoicesFieldOptionsAPI(AbstractBaseAPI):
    def serialize(self):
        return getattr(self.model, self.api_method)()


class DetailAPI(AbstractBaseAPI):
    lookup_field = "id"
    lookup_url_kwarg = "id"
    instance = None

    @classmethod
    def api_update_field_method_name(cls):
        return f"{cls.api_method}_update_fields"

    def api_update_fields(self):
        """Return the model api_update_fields, used for update."""
        return getattr(self.get_instance(), self.api_update_field_method_name())()

    def api_response_serializer(self):
        """Return the model api, used for responses."""
        payload = getattr(self.get_instance(), self.api_method)()
        if not isinstance(payload, dict):
            msg = (
                f"{self.model.__name__}.{self.api_method}() did not return a dictionary"
            )
            raise ImproperlyConfigured(msg)
        return payload

    def serialize(self):
        """Wrap the response serializer, for clarity."""
        return self.api_response_serializer()

    def get_instance(self):
        # TODO support multiple lookup_fields
        self.lookup_kwargs = {self.lookup_field: self.kwargs[self.lookup_url_kwarg]}

        self.validate_lookup_field_values()

        if self.instance is None:
            # TODO use a custom get_object_or_404 that raises a 404 response,
            # instead of using django's default 404 page
            self.instance = get_object_or_404(self.model, **self.lookup_kwargs)

        return self.instance

    def validate_and_update(self):
        """
        Update all fields passed in from json.

        Step 1: Validate
        Step 2: Update
        """
        for key in self.bundle.keys():
            self.validate_bundle(key)
            setattr(self.get_instance(), key, self.bundle[key])

        self.get_instance().save(update_fields=self.bundle.keys())
        self.get_instance().refresh_from_db()


class DetailUpdateAPI(DetailAPI):
    def patch(self, request, *args, **kwargs):
        self.validate_and_update()
        return self.get(request)


class ListAPI(AbstractBaseAPI):
    results_per_page = 25
    lookup_url_kwarg = "id"  # default incase lookup_field is set
    filters = {}
    ordering = []
    search_fields = False
    q_objects = Q()
    count = 0
    page_num = 1
    num_pages = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not isinstance(self.filters, dict):
            raise ImproperlyConfigured(f"{self.codepath}.filters must be type: dict")
        if not isinstance(self.ordering, list):
            raise ImproperlyConfigured(f"{self.codepath}.ordering must be type: list")
        if not isinstance(self.search_fields, bool) and not isinstance(
            self.search_fields, dict
        ):
            raise ImproperlyConfigured(
                f"{self.codepath}.search_filters must be of type bool or dict"
            )

    def _set_base_lookup_kwargs(self):
        # Filters set directly on the class
        self.lookup_kwargs.update(self.filters)

        # Filters set via URL
        if hasattr(self, "lookup_field") and hasattr(self, "lookup_url_kwarg"):
            self.lookup_kwargs.update(
                {self.lookup_field: self.kwargs[self.lookup_url_kwarg]}
            )

        self.validate_lookup_field_values()

    def set_search_lookup_kwargs(self):
        """
        Set generic lookup kwargs based on q and additional GET params.

        For more advanced search use cases, override this method and pass GET
        with any remaining params you want to use classic django filters for.
        """
        if not self.search_fields:
            """If self.search_fields is not set, we don't allow search."""
            return

        self.set_bundle_from_querystring()
        # Whatever is not q or p as a querystring param will
        # be used for key-value search."""
        search_string = self.bundle.get("q", False)
        self.bundle.pop("p", None)
        self.bundle.pop("q", None)

        if search_string and len(search_string):

            the_ors = self.search_fields.get("or", [])
            for attr in the_ors:
                kwarg = {attr + "__icontains": search_string.strip()}
                self.q_objects.add(Q(**kwarg), Q.OR)

            the_ands = self.search_fields.get("ands", [])
            for attr in the_ands:
                kwarg = {attr + "__icontains": search_string.strip()}

        if not self.bundle:
            return

        for key in self.bundle.keys():

            if self.get_field_type(key) == "ManyToManyField":
                if not isinstance(self.bundle[key], list):
                    # TODO simplify this when we move to POST for search.
                    # We do type coersion in set_bundle_from_querystring,
                    # so we need to restore the type of M2M fields as list.
                    self.bundle[key] = [self.bundle[key]]

                self.validate_bundle(key)

            # If we get a list, only support integer values, and skip bundle validation.
            if isinstance(self.bundle[key], list):
                if not all(isinstance(x, int) for x in self.bundle[key]):
                    self.coerce_array_of_integers(key)  # raises 422 if failure
                self.lookup_kwargs.update({f"{key}__in": self.bundle[key]})
                continue

            self.validate_bundle(key)
            self.lookup_kwargs.update({key: self.bundle[key]})

    def get_queryset(self):
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  URL Kwargs
        # If these aren't reset they are polluted by cache (somehow)
        self.lookup_kwargs = {}
        self.q_objects = Q()
        result_set = None

        self._set_base_lookup_kwargs()
        self.set_search_lookup_kwargs()

        try:
            result_set = (
                self.model.objects.filter(self.q_objects, **self.lookup_kwargs)
                .order_by(*self.ordering)
                .distinct()
            )
        except TypeError as e:
            if settings.DEBUG:
                raise HTTP420(f"Error, {self.lookup_kwargs}, {e.__cause__}")
            raise e

        return result_set

    def paginated_results(self):
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ PAGINATION
        queryset = self.get_queryset()

        if settings.DEBUG:
            self.query = str(queryset.query)

        if self.results_per_page is None:
            return queryset

        paginator = Paginator(queryset, self.results_per_page)
        self.page_num = int(self.request.GET.get("p", 1))
        self.num_pages = paginator.num_pages
        self.count = paginator.count

        return paginator.page(self.page_num)

    def serialize(self):

        payload = {
            str(self.name): [
                getattr(instance, self.api_method)()
                for instance in self.paginated_results()
            ],
        }

        if self.results_per_page:
            payload.update(
                {
                    "pagination": dict(
                        count=self.count,
                        pages=self.num_pages,
                        page=self.page_num,
                    )
                }
            )

        if not hasattr(self, "lookup_kwargs"):
            # Debug throws an error in the event there are no lookup_kwargs
            self.lookup_kwargs = {}

        if settings.DEBUG:
            payload.update(
                {
                    "debug": {
                        "bundle": self.bundle,
                        "lookup_kwargs": self.lookup_kwargs,
                        "query": self.query,
                        "q_objs": str(self.q_objects),
                    }
                }
            )
        return payload


class ListCreateAPI(ListAPI):
    def post(self, request, *args, **kwargs):
        for key in self.bundle.keys():
            self.validate_bundle(key)

        new_instance = self.model.objects.create(**self.bundle)
        # TODO except certain errors
        return self.render_to_response(getattr(new_instance, self.api_method)(), 201)
