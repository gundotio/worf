from django.db.models import Manager

import marshmallow.fields
from marshmallow.fields import *  # noqa: F401, F403


class File(marshmallow.fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        return value.url if value.name else None


class Nested(marshmallow.fields.Nested):
    def _serialize(self, nested_obj, attr, obj, **kwargs):
        if isinstance(nested_obj, Manager):
            nested_obj = nested_obj.all()
        return super()._serialize(nested_obj, attr, obj, **kwargs)
