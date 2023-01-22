from django.http import HttpResponse, JsonResponse
from django.template.response import TemplateResponse

from worf.casing import snake_to_camel
from worf.conf import settings
from worf.shortcuts import field_list


def browsable_response(request, response, status_code, view):
    template = "worf/api.html"
    serializer = hasattr(view, "bundle") and view.get_serializer()

    bundle = getattr(view, "bundle", {})
    include = field_list(bundle.get("include", []))
    search = field_list(bundle.get("search", []), delimiter="__")

    filter_fields = [
        (transform_field(field), bool(field in bundle))
        for field in getattr(view, "filter_fields", [])
    ]
    include_fields = [
        (transform_field(field, "."), bool(field in include or not include))
        for field in getattr(view, "include_fields", {}).keys()
    ]
    search_fields = [
        (transform_field(field, "."), bool(field in search or not search))
        for field in getattr(view, "search_fields", [])
    ]

    context = dict(
        content=response.content.decode("utf-8"),
        fields=[
            (
                "Filters",
                sorted(filter_fields),
                len([field for field, active in filter_fields if active]),
            ),
            (
                "Include",
                sorted(include_fields),
                len(include),
            ),
            (
                "Search",
                sorted(search_fields),
                len(search or search_fields) if bundle.get("q") else 0,
            ),
        ],
        lookup_kwargs=getattr(view, "lookup_kwargs", {}),
        payload=bundle,
        response=response,
        serializer=serializer,
        serializer_name=type(serializer).__name__,
        settings=settings,
        view=view,
        view_name=type(view).__name__,
    )

    response = TemplateResponse(request, template, context=context)
    response.status_code = status_code
    response.render()

    return response


def render_response(request, data, status_code, view):
    is_browsable = (
        settings.WORF_BROWSABLE_API
        and "text/html" in request.headers.get("Accept", "")
        and request.GET.get("format") != "json"
    )

    response = (
        JsonResponse(data, json_dumps_params=dict(indent=2 if is_browsable else 0))
        if data != ""
        else HttpResponse()
    )

    response.status_code = status_code

    if is_browsable:
        response = browsable_response(request, response, status_code, view)

    return response


def transform_field(field, delimiter="__"):
    return delimiter.join(map(snake_to_camel, field.split("__")))
