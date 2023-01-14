from worf.assigns import AssignAttributes
from worf.views.base import AbstractBaseAPI


class CreateAPI(AssignAttributes, AbstractBaseAPI):
    create_serializer = None

    def create(self, *args, **kwargs):
        self.instance = self.new_instance()
        self.validate()
        self.save(self.instance, self.bundle)
        self.instance.refresh_from_db()
        return self.instance

    def get_serializer(self, **kwargs):
        if self.create_serializer and self.request.method == "POST":
            return self.create_serializer(**self.get_serializer_kwargs(**kwargs))
        return super().get_serializer(**kwargs)

    def new_instance(self):
        return self.model()

    def post(self, *args, **kwargs):
        instance = self.create(*args, **kwargs)
        result = self.load_serializer().dump(instance) if instance else ""
        return self.render_to_response(result, 201)
