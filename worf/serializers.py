import marshmallow
from marshmallow.decorators import *  # noqa: F401, F403

from django.db.models.fields.files import FieldFile

from worf import fields
from worf.casing import snake_to_camel
from worf.conf import settings
from worf.exceptions import FieldError
from worf.shortcuts import field_list


class SerializeModels:
    include_fields = {}
    serializer = None
    staff_serializer = None

    def get_serializer(self, **kwargs):
        serializer = self.serializer

        if self.staff_serializer and self.request.user.is_staff:  # pragma: no cover
            serializer = self.staff_serializer

        return serializer and serializer(**self.get_serializer_kwargs(**kwargs))

    def get_serializer_context(self):
        return {}

    def get_serializer_kwargs(self, include=[], exclude=[]):
        context = dict(request=self.request, **self.get_serializer_context())
        only = set(field_list(self.bundle.get("fields", [])))
        include = include or field_list(self.bundle.get("include", []))
        exclude = exclude or set(self.include_fields.keys()) - set(include)
        return dict(context=context, only=only, exclude=exclude)

    def load_serializer(self):
        try:
            return self.get_serializer()
        except ValueError as e:
            if str(e).startswith("Invalid fields"):
                invalid_fields = str(e).partition(": ")[2].strip(".")
                raise FieldError(f"Invalid fields: {invalid_fields}")
            raise e  # pragma: no cover

    def serialize(self):
        return self.load_serializer().dump(self.get_instance())


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

    def __init__(self, only=(), *args, **kwargs):
        super().__init__(only=only or None, *args, **kwargs)

    def __call__(self, **kwargs):
        only = self.only
        if self.only and kwargs.get("only"):
            invalid_fields = set(kwargs.get("only")) - self.only
            if invalid_fields:
                raise FieldError(f"Invalid fields: {invalid_fields}")
            only = set(kwargs.get("only"))
        elif kwargs.get("only"):
            only = kwargs.get("only")

        return self.__class__(
            context=kwargs.get("context", self.context),
            dump_only=kwargs.get("dump_only", self.dump_only),
            exclude=set(self.exclude or []) | set(kwargs.get("exclude") or []),
            load_only=kwargs.get("load_only", self.load_only),
            many=kwargs.get("many", self.many),
            only=only,
            partial=kwargs.get("partial", self.partial),
            unknown=kwargs.get("unknown", self.unknown),
        )

    def __repr__(self):
        name = self.__class__.__name__
        kwargs = dict(
            exclude=sorted(self.exclude or []),
            many=self.many,
            only=sorted(self.only or []),
        )
        return f"<{name}({', '.join(f'{k}={v}' for k, v in kwargs.items() if v)})>"

    @property
    def dict_class(self):
        return dict

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = snake_to_camel(field_obj.data_key or field_name)

    class Meta:
        ordered = True
