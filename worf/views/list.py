import operator
import warnings
from functools import reduce

from django.core.exceptions import EmptyResultSet, ImproperlyConfigured
from django.core.paginator import EmptyPage, Paginator
from django.db.models import F, OrderBy, Q

from worf.casing import camel_to_snake
from worf.conf import settings
from worf.filters import apply_filterset, generate_filterset
from worf.shortcuts import list_param
from worf.views.base import AbstractBaseAPI
from worf.views.create import CreateAPI


class ListAPI(AbstractBaseAPI):
    lookup_url_kwarg = "id"  # default incase lookup_field is set
    ordering = []
    filter_fields = []
    search_fields = []
    sort_fields = []
    queryset = None
    filter_set = None
    count = 0
    page_num = 1
    per_page = 25
    max_per_page = None
    num_pages = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        codepath = self.codepath

        if not isinstance(self.ordering, list):  # pragma: no cover
            raise ImproperlyConfigured(f"{codepath}.ordering must be type: list")

        if not isinstance(self.filter_fields, list):  # pragma: no cover
            raise ImproperlyConfigured(f"{codepath}.filter_fields must be type: list")

        if not isinstance(self.search_fields, (dict, list)):  # pragma: no cover
            raise ImproperlyConfigured(f"{codepath}.search_fields must be type: list")

        if not isinstance(self.sort_fields, list):  # pragma: no cover
            raise ImproperlyConfigured(f"{codepath}.sort_fields must be type: list")

        # generate a default filterset if a custom one was not provided
        if self.filter_set is None:
            self.filter_set = generate_filterset(self.model, self.queryset)

        # support deprecated search_fields and/or dict syntax (note that `and` does nothing)
        if isinstance(self.search_fields, dict):  # pragma: no cover - deprecated
            warnings.warn(
                f"Passing a dict to {codepath}.search_fields is deprecated. Pass a list instead."
            )
            self.search_fields = self.search_fields.get("or", [])

    def get(self, *args, **kwargs):
        return self.render_to_response()

    def set_base_lookup_kwargs(self):
        if hasattr(self, "lookup_field") and hasattr(self, "lookup_url_kwarg"):
            self.lookup_kwargs[self.lookup_field] = self.kwargs[self.lookup_url_kwarg]

    def set_search_lookup_kwargs(self):
        """
        Set generic lookup kwargs based on q and additional GET params.

        For more advanced search use cases, override this method and pass GET
        with any remaining params you want to use classic django filters for.
        """
        if not self.filter_fields and not self.search_fields:
            return

        # Whatever is not q or page as a querystring param will
        # be used for key-value search.
        query = self.bundle.pop("q", "").strip()

        self.bundle.pop("page", None)
        self.bundle.pop("p", None)

        if query:
            search_icontains = (
                Q(**{f"{search_field}__icontains": query})
                for search_field in self.search_fields
            )
            self.search_query = reduce(operator.or_, search_icontains)

        if not self.filter_fields or not self.bundle:  # pragma: no cover
            return

        for key in self.bundle.keys():
            filter_key = key[:-1] if key.endswith("!") else key

            if filter_key not in self.filter_fields:
                continue

            value = self.bundle[key]

            # support passing `in` and `range` as lists
            if isinstance(value, list):
                if filter_key.endswith("__in") or filter_key.endswith("__range"):
                    value = ",".join(str(item) for item in value)

            self.lookup_kwargs[key] = value

    def get_queryset(self):
        if self.queryset is None:
            return self.model.objects.all()
        return self.queryset.all()

    def get_processed_queryset(self):
        self.lookup_kwargs = {}
        self.search_query = Q()

        self.set_base_lookup_kwargs()
        self.set_search_lookup_kwargs()

        lookups = self.lookup_kwargs.items()
        filterset_kwargs = {k: v for k, v in lookups if not isinstance(v, list)}
        list_kwargs = {k: v for k, v in lookups if isinstance(v, list)}
        ordering = self.get_ordering()

        queryset = (
            apply_filterset(self.filter_set, self.get_queryset(), filterset_kwargs)
            .filter(self.search_query)
            .distinct()
        )

        for key, value in list_kwargs.items():
            for item in value:
                queryset = (
                    queryset.exclude(**{key.rstrip("!"): item})
                    if key.endswith("!")
                    else queryset.filter(**{key: item})
                )

        if ordering:
            queryset = queryset.order_by(*ordering)

        return queryset

    def get_ordering(self):
        ordering = []

        for sort in list_param(self.bundle.get("sort", [])):
            field = "__".join(map(camel_to_snake, sort.lstrip("-").split(".")))
            if field not in self.sort_fields:
                continue
            ordering.append(self.get_sort_field(field, descending=sort[0] == "-"))

        return ordering or self.ordering

    def get_sort_field(self, field, descending=False):
        return OrderBy(F(field), descending=descending)

    def paginated_results(self):
        queryset = self.get_processed_queryset()
        request = self.request

        if settings.WORF_DEBUG:  # pragma: no cover
            try:
                self.query = str(queryset.query)
            except EmptyResultSet:
                self.query = None

        default_per_page = getattr(self, "results_per_page", self.per_page)
        per_page = max(int(request.GET.get("perPage") or default_per_page), 1)
        max_per_page = self.max_per_page or default_per_page
        paginator = Paginator(queryset, min(per_page, max_per_page))

        self.page_num = int(request.GET.get("page") or request.GET.get("p") or 1)
        if self.page_num < 1:
            self.page_num = 1

        self.num_pages = paginator.num_pages
        self.count = paginator.count

        try:
            return paginator.page(self.page_num)
        except EmptyPage:
            return []

    def serialize(self):
        serializer = self.load_serializer()

        payload = {str(self.name): serializer(many=True).dump(self.paginated_results())}

        if self.per_page:
            payload["pagination"] = dict(
                count=self.count,
                pages=self.num_pages,
                page=self.page_num,
            )

        if settings.WORF_DEBUG:  # pragma: no cover
            payload["debug"] = {
                "bundle": self.bundle,
                "lookup_kwargs": getattr(self, "lookup_kwargs", {}),
                "query": self.query,
                "search_query": str(self.search_query),
                "serializer": str(serializer).strip("<>"),
            }

        return payload


class ListCreateAPI(CreateAPI, ListAPI):
    pass
