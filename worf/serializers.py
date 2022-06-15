import marshmallow

from django.core.exceptions import ImproperlyConfigured
from django.db.models.fields.files import FieldFile

from worf import fields  # noqa: F401
from worf.casing import snake_to_camel
from worf.conf import settings


class SerializerOptions(marshmallow.SchemaOpts):
    def __init__(self, meta, **kwargs):
        super().__init__(meta, **kwargs)

        defaults = settings.WORF_SERIALIZER_DEFAULT_OPTIONS
        defaults["ordered"] = defaults.get("ordered", True)

        for key, value in defaults.items():
            setattr(self, key, getattr(meta, key, value))

        fields = getattr(meta, "fields", [])
        writable = getattr(meta, "writable", [])

        if writable:
            self.dump_only = list(set(fields) - set(writable))


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

    def __call__(self, **kwargs):
        return type(self)(
            context=kwargs.get("context", self.context),
            dump_only=kwargs.get("dump_only", self.dump_only),
            exclude=kwargs.get("exclude", self.exclude),
            load_only=kwargs.get("load_only", self.load_only),
            many=kwargs.get("many", self.many),
            only=kwargs.get("only", self.only),
            partial=kwargs.get("partial", self.partial),
            unknown=kwargs.get("unknown", self.unknown),
        )

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
