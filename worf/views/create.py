from django.core.exceptions import ValidationError

from worf.casing import snake_to_camel
from worf.views.base import AbstractBaseAPI


class CreateAPI(AbstractBaseAPI):

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
            if key not in self.serializer.create():
                raise ValidationError(
                    "{} not allowed when creating {}".format(
                        snake_to_camel(key), self.name
                    )
                )

        if set(self.bundle.keys()) != set(self.serializer.create()):
            raise ValidationError(
                "{} are required to create {}".format(
                    [snake_to_camel(key) for key in self.serializer.create()], self.name
                )
            )
