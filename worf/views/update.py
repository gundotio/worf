from worf.assigns import AssignAttributes
from worf.lookups import FindInstance
from worf.views.base import AbstractBaseAPI


class UpdateAPI(AssignAttributes, FindInstance, AbstractBaseAPI):
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
