from worf.assigns import AssignAttributes
from worf.views.base import AbstractBaseAPI


class CreateAPI(AssignAttributes, AbstractBaseAPI):
    create_serializer = None

    def create(self):
        self.instance = self.new_instance()
        self.validate()
        self.save(self.instance, self.bundle)
        self.instance.refresh_from_db()
        return self.instance

    def get_serializer(self):
        if self.create_serializer and self.request.method == "POST":
            return self.create_serializer(context=self.get_serializer_context())
        return super().get_serializer()

    def new_instance(self):
        return self.model()

    def post(self, request, *args, **kwargs):
        return self.render_to_response(self.get_serializer().read(self.create()), 201)
