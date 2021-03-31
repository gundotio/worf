from django.conf import settings
from django.http import Http404
from worf.exceptions import HTTP404


def get_instance_or_http404(model, *args, **kwargs):
    try:
        return getattr(getattr(model, "objects"), "get")(*args, **kwargs)
    except model.DoesNotExist:
        if settings.DEBUG:
            raise Http404(
                "No {} matches the given query.".format(model._meta.object_name)
            )
        raise HTTP404()
