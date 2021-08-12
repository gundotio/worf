from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import Paginator, EmptyPage
from django.db.models import ManyToManyField, Q

from worf.casing import camel_to_snake, clean_lookup_keywords
from worf.exceptions import HTTP420
from worf.filters import apply_filterset, generate_filterset
from worf.views.base import AbstractBaseAPI
from worf.views.create import CreateAPI


class ListAPI(AbstractBaseAPI):
    results_per_page = 25
    lookup_url_kwarg = "id"  # default incase lookup_field is set
    filters = {}
    ordering = []
    filter_fields = None
    search_fields = None
    sort_fields = None
    queryset = None
    q_objects = Q()
    filter_set = None
    count = 0
    page_num = 1
    num_pages = 1

    def get(self, request, *args, **kwargs):
        return self.render_to_response()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not isinstance(self.filters, dict):
            raise ImproperlyConfigured(f"{self.codepath}.filters must be type: dict")
        if not isinstance(self.ordering, list):
            raise ImproperlyConfigured(f"{self.codepath}.ordering must be type: list")
        if self.filter_fields is not None and not isinstance(self.filter_fields, list):
            raise ImproperlyConfigured(
                f"{self.codepath}.filter_fields must be type: list"
            )
        if self.search_fields is not None and not isinstance(self.search_fields, dict):
            raise ImproperlyConfigured(
                f"{self.codepath}.search_fields must be type: dict"
            )
        if self.sort_fields is not None and not isinstance(self.sort_fields, list):
            raise ImproperlyConfigured(
                f"{self.codepath}.sort_fields must be type: list"
            )
        if self.filter_set is None:
            self.filter_set = generate_filterset(self.model)

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
        if self.search_fields is None:
            """If self.search_fields is not set, we don't allow search."""
            return

        self.set_bundle_from_querystring()
        # Whatever is not q or page as a querystring param will
        # be used for key-value search.
        search_string = self.bundle.get("q", False)
        self.bundle.pop("page", None)
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

        if not self.filter_fields or not self.bundle:
            return

        for key in self.bundle.keys():
            field = clean_lookup_keywords(key)
            if key not in self.filter_fields:
                continue

            if isinstance(self.model._meta.get_field(field), ManyToManyField):
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

                self.lookup_kwargs.update(
                    {f"{key}__in": ",".join(str(value) for value in self.bundle[key])}
                )

                continue

            self.validate_bundle(key)
            self.lookup_kwargs.update({key: self.bundle[key]})

    def get_queryset(self):
        return (self.queryset or self.model.objects).all()

    def get_processed_queryset(self):
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  URL Kwargs
        # If these aren't reset they are polluted by cache (somehow)
        queryset = self.get_queryset()

        self.lookup_kwargs = {}
        self.q_objects = Q()

        self._set_base_lookup_kwargs()
        self.set_search_lookup_kwargs()

        order_by = self.ordering
        if self.request.GET.get("sort"):
            sort = self.parse_sort(self.request.GET.getlist("sort"))
            if set([s.lstrip("-") for s in sort]).issubset(self.sort_fields):
                order_by = sort

        try:
            queryset = (
                apply_filterset(self.filter_set, queryset, self.lookup_kwargs)
                .filter(self.q_objects)
                .order_by(*order_by)
                .distinct()
            )
        except TypeError as e:
            if settings.DEBUG:
                raise HTTP420(f"Error, {self.lookup_kwargs}, {e.__cause__}")
            raise e

        return queryset

    def paginated_results(self):
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ PAGINATION
        queryset = self.get_processed_queryset()
        request = self.request

        if settings.DEBUG:
            self.query = str(queryset.query)

        if self.results_per_page is None:
            return queryset

        paginator = Paginator(queryset, self.results_per_page)

        self.page_num = int(request.GET.get("page") or request.GET.get("p") or 1)
        if self.page_num < 1:
            self.page_num = 1

        self.num_pages = paginator.num_pages
        self.count = paginator.count

        try:
            return paginator.page(self.page_num)
        except EmptyPage:
            return []

    def parse_sort(self, fields):
        return [self.transform_sort(field) for field in fields]

    def transform_sort(self, field):
        prefix = "-" if field[0] == "-" else ""
        return prefix + "__".join(map(camel_to_snake, field.lstrip("-").split(".")))

    def serialize(self):
        serializer = self.get_serializer()

        payload = {
            str(self.name): [
                serializer.read(instance) for instance in self.paginated_results()
            ]
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

        if not settings.DEBUG:
            return payload

        if not hasattr(self, "lookup_kwargs"):
            # Debug throws an error in the event there are no lookup_kwargs
            self.lookup_kwargs = {}

        payload.update(
            {
                "debug": {
                    "api_method": self.api_method,
                    "bundle": self.bundle,
                    "lookup_kwargs": self.lookup_kwargs,
                    "query": self.query,
                    "q_objs": str(self.q_objects),
                    "serializer": str(serializer),
                }
            }
        )

        return payload


class ListCreateAPI(ListAPI, CreateAPI):
    pass
