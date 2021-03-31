from django.conf import settings
from worf.exceptions import HTTP404


def get_instance_or_http404(model, **kwargs):
    try:
        return getattr(getattr(model, "objects"), "get")(**kwargs)
    except model.DoesNotExist as e:
        if settings.DEBUG:
            raise e
        raise HTTP404
