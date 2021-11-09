from django.core.exceptions import ValidationError

from worf.views.base import AbstractBaseAPI


class CreateAPI(AbstractBaseAPI):
    def serialize(self):
        return {}

    def post(self, request, *args, **kwargs):
        new_instance = self.create()
        serializer = self.get_serializer()
        return self.render_to_response(serializer.read(new_instance), 201)

    def create(self):
        self.validate()

        return self.model.objects.create(**self.bundle)

    def validate(self):
        create_fields = self.get_serializer().create()

        for key in self.bundle.keys():
            self.validate_bundle(key)
            # ignore create_fields for now if it's empty
            # this should be moved into validate bundle
            if create_fields and key not in create_fields:
                raise ValidationError(
                    f"{self.keymap[key]} not allowed when creating {self.name}"
                )
