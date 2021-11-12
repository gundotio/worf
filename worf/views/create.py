from worf.assigns import AssignAttributes
from worf.views.base import AbstractBaseAPI


class CreateAPI(AssignAttributes, AbstractBaseAPI):
    def create(self):
        instance = self.get_instance()
        self.validate()
        self.save(instance, self.bundle)
        instance.refresh_from_db()
        return instance

    def get_instance(self):
        return self.model()

    def post(self, request, *args, **kwargs):
        new_instance = self.create()
        serializer = self.get_serializer()
        return self.render_to_response(serializer.read(new_instance), 201)
