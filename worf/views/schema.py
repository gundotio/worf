import importlib
from typing import List, Optional

from django.conf import settings
from django.http import JsonResponse
from django.urls import URLPattern

from worf.schema import SchemaGenerator
from worf.views import AbstractBaseAPI


class SchemaView(AbstractBaseAPI):
    generator: SchemaGenerator = None
    urlpatterns: Optional[List[URLPattern]] = None

    def as_json(self, *args, **kwargs):
        if self.generator is None:
            self.generator = SchemaGenerator(
                title="Your API title",
                base_url="http://localhost",
            )

        if self.urlpatterns is None:
            self._resolve_url_patterns()

        schema = self.generator.get_schema()

        return JsonResponse(schema)

    def _resolve_url_patterns(self):
        urlconf = settings.ROOT_URLCONF
        self.generator.urlpatterns = importlib.import_module(urlconf).urlpatterns
