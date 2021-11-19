import marshmallow

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models.fields.files import FieldFile

from worf import fields  # noqa: F401
from worf.casing import snake_to_camel


class SerializerOptions(marshmallow.SchemaOpts):
    def __init__(self, meta, **kwargs):
        super().__init__(meta, **kwargs)

        meta_defaults = getattr(settings, "WORF_SERIALIZER_DEFAULT_OPTIONS", {})

        for key, default_value in meta_defaults.items():
            setattr(self, key, getattr(meta, key, default_value))


class Serializer(marshmallow.Schema):
    """
    Serializers are basically marshmallow schemas with extra handling for
    Django models/managers, some tweaks to field naming/ordering and the option
    to supply some meta defaults via Django settings.

    The read/write methods are relics of our interim serialization strategy
    they're analogous with marshmallow dump/load, but a bit less flexible.

    Marshmallow is primarily used for field filtering right now, worf coerces
    values itself, but we might delegated more to marshmallow later.
    """

    OPTIONS_CLASS = SerializerOptions

    TYPE_MAPPING = {
        **marshmallow.Schema.TYPE_MAPPING,
        FieldFile: fields.File,
    }

    def __repr__(self):
        return f"<{self.__class__.__name__}()>"

    @property
    def dict_class(self):
        return dict

    def list(self, items):
        return [self.read(item) for item in items]

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = snake_to_camel(field_obj.data_key or field_name)

    def read(self, obj):
        return self.dump(obj)

    def write(self):
        return list(self.load_fields.keys())

    class Meta:
        ordered = True


class LegacySerializer:
    def __init__(self, model_class, api_method):
        self.api_method = api_method
        self.model_class = model_class

    def __repr__(self):
        return f'<{self.__class__.__name__}(model_class={self.model_class.__name__}, api_method="{self.api_method}")>'

    def list(self, items):
        return [self.read(item) for item in items]

    def read(self, obj):
        payload = getattr(obj, self.api_method)()
        if not isinstance(payload, dict):
            msg = f"{obj.__name__}.{self.api_method}() did not return a dictionary"
            raise ImproperlyConfigured(msg)
        return payload

    def write(self):
        return getattr(self.model_class(), f"{self.api_method}_update_fields")()
