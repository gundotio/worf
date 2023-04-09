import re
from typing import Callable, Generator, List, Optional, Tuple, Union

from django.contrib.admindocs.views import simplify_regex
from django.urls import URLPattern, resolve

from worf.schema.openapi import OpenApiGenerator, SchemaMetadata
from worf.views import AbstractBaseAPI, CreateAPI, DetailAPI, ListAPI, UpdateAPI

_PATH_PARAMETER_COMPONENT_RE = re.compile(
    r"<(?:(?P<converter>[^>:]+):)?(?P<parameter>\w+)>"
)


class SchemaGenerator:
    def __init__(
        self,
        title: str,
        base_url: str,
        urlpatterns: Optional[List[URLPattern]] = None,
        version: str = "1.0.0",
    ):
        self.openapi = OpenApiGenerator(title=title, base_url=base_url, version=version)
        self.urlpatterns = urlpatterns
        self.endpoints: Optional[List[SchemaMetadata]] = None

    def get_schema(self, _format="json") -> Union[dict, str]:
        if self.endpoints is None:
            self.endpoints = list(self.get_api_endpoints())

        return self.openapi.get_schema(self.endpoints, _format)

    def get_api_endpoints(self) -> Generator[SchemaMetadata, None, None]:
        """
        A generator of SchemaMetadata. For each unique endpoint (e.g. GET /users)
        one SchemaMetadata will be yielded.
        """
        # print()
        # for patt in self.urlpatterns:
        #     print(patt.__dict__)
        api_endpoints = list(self._get_api_endpoints_from_url_patterns())

        for group in self._group_by_common_prefixes(api_endpoints):
            for endpoint in group:
                path, method, view_class, doc = endpoint
                tag = self._resolve_endpoint_tag_based_on_path(path)
                yield SchemaMetadata(
                    path=path,
                    method=method,
                    description=self._resolve_endpoint_description(path, method, doc),
                    serializer=view_class.serializer,
                    is_list=issubclass(view_class, ListAPI),
                    model=view_class.model,
                    tag=tag,
                )

    def _get_api_endpoints_from_url_patterns(
        self,
    ) -> Generator[Tuple[str, str, AbstractBaseAPI, Optional[str]], None, None]:
        """
        A generator that yields resolves API endpoints based on the urlpatterns,
        and yields metadata for each endpoint.

        Yields:
        - path: /profiles/
        - method: GET | POST | PUT | PATCH | DELETE
        - view_class: tests.views.ProfileList
        - doc: the doc of the callback function
        """
        for pattern in self.urlpatterns:
            path_regex = str(pattern.pattern)
            if isinstance(pattern, URLPattern):
                path, callback, view_class = self._get_metadata_from_path(path_regex)
                if path is None:
                    continue

                for method in self.get_allowed_methods(view_class):
                    yield path, method, view_class, callback.__doc__

    @staticmethod
    def _resolve_endpoint_tag_based_on_path(path: str) -> str:
        return path.split("/")[1]

    @staticmethod
    def _resolve_endpoint_description(path: str, method: str, doc: Optional[str]):
        if doc:
            return doc

        description = f"{method.lower()} {path[1:-1]}"
        description = description.replace("/{", "[").replace("}", "]").replace("/", ".")
        return description

    @staticmethod
    def _group_by_common_prefixes(api_endpoints):
        """Group the given endpoints by their common prefixes."""
        groups = []
        current_group = []
        current_prefix = None

        for endpoint in api_endpoints:
            path, method, view_class, _ = endpoint
            if current_prefix is None:
                current_prefix = path
            elif not path.startswith(current_prefix):
                groups.append(current_group)
                current_group = []
                current_prefix = path

            current_group.append(endpoint)

        if current_group:
            groups.append(current_group)

        return groups

    def _get_metadata_from_path(
        self, path_regex: str
    ) -> (str, Callable, AbstractBaseAPI):
        path, resolve_path = self._get_path_from_regex(path_regex)
        callback = resolve(resolve_path).func
        if self._is_schema_view(callback):
            return None, None, None  # skip the schema view
        view_class = callback.view_class

        if not issubclass(view_class, AbstractBaseAPI):
            return None, None, None  # skip any view that is not a worf view

        return path, callback, view_class

    @staticmethod
    def get_allowed_methods(view_class):
        """Returns a list of the valid HTTP methods for this endpoint."""
        methods = []
        if issubclass(view_class, CreateAPI):
            methods.append("POST")
        if issubclass(view_class, ListAPI):
            methods.append("GET")
        if issubclass(view_class, DetailAPI):
            methods.extend(["GET"])
        if issubclass(view_class, UpdateAPI):
            methods.extend(["PUT", "PATCH"])
        if issubclass(view_class, DetailAPI):
            methods.append("DELETE")

        return methods

    @staticmethod
    def _get_path_from_regex(path_regex) -> Tuple[str, str]:
        """
        Given a URL conf regex, returns:
        - path: the path to be used in openapi docs annotations
        - resolve_path: a modified path where identifiers inside '{}' are replaced
        with actual values in order to be able to resolve the callback with resolve().
        The resolve_path is required because the resolve() function requires actual
        values (a UUID or an integer) instead of placeholders.

        E.g.: If regex_path is 'profiles/<uuid:id>/', then:
        - path = /profiles/{id}/
        - resolve_path = /profiles/075194d3-6885-417e-a8a8-6c931e272f00/
        """
        path = simplify_regex(path_regex)

        random_uuid = "075194d3-6885-417e-a8a8-6c931e272f00"
        random_int_or_str = "1"
        replace_value = random_uuid if "uuid" in path_regex else random_int_or_str

        resolve_path = re.sub(_PATH_PARAMETER_COMPONENT_RE, replace_value, path)
        path = re.sub(_PATH_PARAMETER_COMPONENT_RE, r"{\g<parameter>}", path)
        return path, resolve_path

    @staticmethod
    def _is_schema_view(callback):
        # Avoid import cycle on SchemaView
        from worf.views.schema import SchemaView

        if not hasattr(callback, "__self__"):
            return False
        return issubclass(callback.__self__.__class__, SchemaView)

    @staticmethod
    def _endpoint_ordering(endpoint):
        path, method, callback, view_class = endpoint
        method_priority = {"GET": 0, "POST": 1, "PUT": 2, "PATCH": 3, "DELETE": 4}.get(
            method, 5
        )

        return (method_priority,)
