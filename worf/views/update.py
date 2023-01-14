from worf.assigns import AssignAttributes
from worf.lookups import FindInstance
from worf.views.base import AbstractBaseAPI


class UpdateAPI(AssignAttributes, FindInstance, AbstractBaseAPI):
    update_serializer = None

    def get_serializer(self, **kwargs):
        if self.update_serializer and self.request.method in ("PATCH", "PUT"):
            return self.update_serializer(**self.get_serializer_kwargs(**kwargs))
        return super().get_serializer(**kwargs)

    def patch(self, *args, **kwargs):
        self.update(*args, **kwargs)
        return self.render_to_response()

    def put(self, *args, **kwargs):
        self.update(*args, **kwargs)
        return self.render_to_response()

    def update(self, *args, **kwargs):
        instance = self.get_instance()
        self.validate()
        self.save(instance, self.bundle)
        instance.refresh_from_db()
        return instance
