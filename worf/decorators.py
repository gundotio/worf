from functools import update_wrapper
from worf.views.base import AbstractBaseAPI


def api(func=None, bases=AbstractBaseAPI):
    def wrapper(func):
        view = type(func.__name__, (bases,), {"get": func})
        view.__module__ = func.__module__
        return update_wrapper(view.as_view(), func)

    if func is not None:
        return wrapper(func)

    return wrapper
