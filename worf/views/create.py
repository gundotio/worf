from django.core.exceptions import ValidationError

from worf.casing import snake_to_camel
from worf.views.base import AbstractBaseAPI


class CreateAPI(AbstractBaseAPI):
    def serialize(self):
        return {}

    def post(self, request, *args, **kwargs):

        # Deprecate ------------------------------------------------------------
        if self.serializer is None:
            for key in self.bundle.keys():
                self.validate_bundle(key)

            new_instance = self.model.objects.create(**self.bundle)
            return self.render_to_response(
                getattr(new_instance, self.api_method)(), 201
            )
        # ------------------------------------------------------------ Deprecate

        for key in self.bundle.keys():
            self.validate_bundle(key)
            # this should be moved into validate bundle
            if key not in self.serializer.create():
                raise ValidationError(
                    "{} not allowed when creating {}".format(
                        snake_to_camel(key), self.name
                    )
                )

        new_instance = self.model.objects.create(**self.bundle)
        return self.render_to_response(self.serializer(new_instance).read(), 201)
