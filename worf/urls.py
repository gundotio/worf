from types import FunctionType

from django.urls import include, path


def api(base, view, includes=[], **kwargs):
    if isinstance(view, list):
        return path(base, include(view), **kwargs)
    view_class = getattr(view, "view_class", view)
    init_kwargs = getattr(view, "view_initkwargs", {})
    view_func = view if isinstance(view, FunctionType) else view.as_view(**init_kwargs)
    actions = []
    if hasattr(view_class, "perform_action"):
        actions = [
            path(
                f"{action.replace('_', '-')}/",
                view_class.as_view(action=action, **init_kwargs),
                name=f"{kwargs['name']}_{action}" if "name" in kwargs else None,
            )
            for action in getattr(view_class, "actions", [])
        ]
    if not actions and not includes:
        return path(base, view_func, **kwargs)
    return path(base, include([path("", view_func, **kwargs), *includes, *actions]))
