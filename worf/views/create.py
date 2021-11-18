from worf.assigns import AssignAttributes
from worf.views.base import AbstractBaseAPI


class CreateAPI(AssignAttributes, AbstractBaseAPI):
    create_serializer = None

    def create(self):
        instance = self.get_instance()
        self.validate()
        self.save(instance, self.bundle)
        instance.refresh_from_db()
        return instance

    def get_instance(self):
        return self.model()

    def get_serializer(self):
        if self.create_serializer and self.request.method == "POST":
            return self.create_serializer()
        return super().get_serializer()

    def post(self, request, *args, **kwargs):
        new_instance = self.create()
        serializer = self.get_serializer()
        return self.render_to_response(serializer.read(new_instance), 201)
