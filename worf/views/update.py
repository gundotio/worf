from worf.assigns import AssignAttributes
from worf.lookups import FindInstance
from worf.views.base import AbstractBaseAPI


class UpdateAPI(AssignAttributes, FindInstance, AbstractBaseAPI):
    update_serializer = None

    def get_serializer(self):
        if self.update_serializer and self.request.method in ("PATCH", "PUT"):
            return self.update_serializer()
        return super().get_serializer()

    def patch(self, request, *args, **kwargs):
        self.update()
        return self.render_to_response()

    def put(self, request, *args, **kwargs):
        self.update()
        return self.render_to_response()

    def update(self):
        instance = self.get_instance()
        self.validate()
        self.save(instance, self.bundle)
        instance.refresh_from_db()
        return instance
