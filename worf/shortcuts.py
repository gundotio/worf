import subprocess

from django.conf import settings
from django.http import Http404
from worf import __version__
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


def get_current_version():
    try:
        hash = (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
            .strip()
            .decode()
        )
        return f"{__version__}@{hash}"
    except:  # pragma: no cover # noqa E722 Dont crash for any reason whatsoever
        return __version__
