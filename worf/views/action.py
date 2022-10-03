from worf.exceptions import ActionError
from worf.lookups import FindInstance
from worf.views.base import AbstractBaseAPI


class ActionAPI(FindInstance, AbstractBaseAPI):
    actions = []

    def dispatch(self, request, *args, **kwargs):
        if "action" in kwargs and request.method != "PUT":
            return self.http_method_not_allowed(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

    def perform_action(self, request, *args, **kwargs):
        action = kwargs["action"].replace("-", "_")
        if action not in self.actions:
            raise ActionError(f"Invalid action: {kwargs['action']}")
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

    def put(self, request, *args, **kwargs):
        if "action" in kwargs:
            self.perform_action(request, *args, **kwargs)
            return self.render_to_response()
        return super().put(request, *args, **kwargs)
