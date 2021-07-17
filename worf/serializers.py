import json
from django.core.exceptions import ImproperlyConfigured


def deserialize(response):
    return json.loads(response.content.decode("UTF-8"))


class Serializer:
    def create(self):
        return []

    def read(self, model):
        return {}

    def write(self):
        return []


class LegacySerializer(Serializer):
    def __init__(self, model_class, api_method):
        self.api_method = api_method
        self.model_class = model_class

    def read(self, model):
        payload = getattr(model, self.api_method)()
        if not isinstance(payload, dict):
            msg = f"{model.__name__}.{self.api_method}() did not return a dictionary"
            raise ImproperlyConfigured(msg)
        return payload

    def write(self):
        return getattr(self.model_class(), f"{self.api_method}_update_fields")()
