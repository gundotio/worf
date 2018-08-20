"""
This is experimental and unused.

In order to produce a browsable API, documentation, and/or, open api schema,
we need to know what endpoints are an API endpoint.

We also could, with _relative_ simplicity, generate automated tests for these
endpoints based on the contract described by our api_update_fields method and
the view's http_method_names.

Worth spending some more time here.
"""

import re
from importlib import import_module

from django.conf import settings
from django.urls import URLPattern, URLResolver


class Generator:
    def __init__(self):
        urlconf = settings.API_URL_CONF

        if isinstance(urlconf, str):
            urls = import_module(urlconf)

        self.patterns = urls.urlpatterns

    def get_endpoints(self):
        pass
