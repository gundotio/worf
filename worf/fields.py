from marshmallow import fields, utils
from marshmallow.exceptions import ValidationError
from marshmallow.fields import *  # noqa: F401, F403

from django.db.models import Manager


class SerializeMissing:
    def __init__(self, *args, **kwargs):
        if "dump_default" not in kwargs:
            kwargs["dump_default"] = [] if kwargs.get("many") else None
        return super().__init__(*args, **kwargs)


class SerializeQuerysets:
    def _serialize(self, nested_obj, attr, obj, **kwargs):
        if isinstance(nested_obj, Manager):
            nested_obj = nested_obj.all()
        return super()._serialize(nested_obj, attr, obj, **kwargs)


class Field(SerializeMissing, fields.Field):
    pass


class File(Field):
    _CHECK_ATTRIBUTE = False

    def __init__(self, serialize=None, deserialize=None, **kwargs):
        super().__init__(**kwargs)
        self.serialize_func = serialize and utils.callable_or_raise(serialize)
        self.deserialize_func = deserialize and utils.callable_or_raise(deserialize)

    def _serialize(self, value, attr, obj, **kwargs):
        if self.serialize_func:
            return self._call_or_raise(self.serialize_func, obj, attr)
        return value.url if value.name else None

    # Worf serializers are not really used for deserialization yet, so no cover

    def _deserialize(self, value, attr, data, **kwargs):  # pragma: no cover
        if self.deserialize_func:
            return self._call_or_raise(self.deserialize_func, value, attr)
        return value

    def _call_or_raise(self, func, value, attr):
        if len(utils.get_func_args(func)) > 1:  # pragma: no cover
            if self.parent.context is None:
                msg = f"No context available for Function field {attr!r}"
                raise ValidationError(msg)
            return func(value, self.parent.context)
        return func(value)


class Nested(SerializeQuerysets, fields.Nested):
    pass


class Pluck(SerializeQuerysets, fields.Pluck):
    pass


for field in map(fields.__dict__.get, fields.__all__):
    if fields.Field not in field.__bases__ or SerializeMissing in field.__bases__:
        continue
    field.__bases__ = (SerializeMissing, *field.__bases__)


__all__ = [
    *fields.__all__,
    "File",
]
