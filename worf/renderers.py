from django.http import HttpResponse, JsonResponse
from django.template.response import TemplateResponse

from worf.conf import settings


def browsable_response(request, response, status_code=200):
    template = "worf/api.html"
    context = dict(
        content=response.content.decode("utf-8"),
        response=response,
        settings=settings,
    )

    response = TemplateResponse(request, template, context=context)
    response.status_code = status_code
    response.render()

    return response


def render_response(request, data, status_code=200):
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
        response = browsable_response(request, response, status_code)

    return response
