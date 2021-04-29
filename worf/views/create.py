from django.core.exceptions import ValidationError

from worf.casing import snake_to_camel
from worf.views.base import AbstractBaseAPI


class CreateAPI(AbstractBaseAPI):
    def serialize(self):
        return {}

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer()

        create_fields = serializer.create()
        for key in self.bundle.keys():
            self.validate_bundle(key)
            # ignore create_fields for now if it's empty
            # this should be moved into validate bundle
            if create_fields and key not in create_fields:
                raise ValidationError(
                    "{} not allowed when creating {}".format(
                        snake_to_camel(key), self.name
                    )
                )

        new_instance = self.model.objects.create(**self.bundle)
        return self.render_to_response(serializer.read(new_instance), 201)
