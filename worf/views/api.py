from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import Paginator
from django.db.models import Q

from django.shortcuts import get_object_or_404

from worf.views.base import AbstractBaseAPI
from worf.exceptions import HTTP420


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
        instance = self.get_instance()
        fields = self.bundle.keys()

        for field in fields:
            self.validate_bundle(field)
            setattr(instance, field, self.bundle[field])

        instance.save(update_fields=fields)
        instance.refresh_from_db()


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
