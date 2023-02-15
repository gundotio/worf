from worf.exceptions import ActionError, MethodNotAllowed, NotFound
from worf.lookups import FindInstance
from worf.views.base import AbstractBaseAPI


class ActionAPI(FindInstance, AbstractBaseAPI):
    action = None
    actions = []

    def perform_action(self, request, *args, **kwargs):
        action = kwargs.get("action", self.action or "").replace("-", "_")
        instance = self.get_instance()
        if hasattr(self, action):
            return getattr(self, action)(request, **self.bundle, user=request.user)
        try:
            getattr(instance, action)(**self.bundle, user=request.user)
        except TypeError as e:
            if "unexpected keyword argument 'user'" not in str(e):
                raise ActionError(f"Invalid arguments: {e}")
            getattr(instance, action)(**self.bundle)
        return instance

    def perform_dispatch(self, request, *args, **kwargs):
        action = kwargs.get("action", self.action or "").replace("-", "_")
        if not action:
            return super().perform_dispatch(request, *args, **kwargs)
        if action not in self.actions:  # pragma: no cover
            raise NotFound
        if request.method != "PUT":
            raise MethodNotAllowed(allowed_methods=["PUT"])
        return super().perform_dispatch(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        if "action" in kwargs or self.action is not None:
            self.perform_action(request, *args, **kwargs)
            return self.render_to_response()
        return super().put(request, *args, **kwargs)
