import json
import warnings

from random import choice
from string import ascii_uppercase

from django.utils import timezone

from worf.casing import camel_to_snake, snake_to_camel


def bundle_factory(instance, serializer="api_update_fields"):  # pragma: no cover
    # TODO consider extending the django test client with these methods.
    # TODO handle Choices fields; otherwise we may pass invalid values
    """
    Return a valid python dictionary for api testing.

    @param instance the model instance we are testing against
    @param serializer (optional) the model method that sets update_fields

    Limitations:
        - Does not generate nor include any FK's, 1:1's, M2M fields
        - Only sets up valid data. Should always 200
    """
    bundle = dict()

    sequence = 0
    for field in getattr(instance, serializer)():
        sequence += 1
        type = instance._meta.get_field(field).get_internal_type()

        if type in ["OneToOneField", "ForeignKey", "ManyToManyField"]:
            # TODO handle m2ms
            continue

        value = None
        if type in ["CharField", "TextField", "EmailField", "SlugField"]:
            if type == "TextField":
                value = "something {}".format(sequence)
            elif type == "EmailField":
                value = "test{}@example.com".format(sequence)
            else:
                max_len = instance._meta.get_field(field).max_length
                value = "".join(choice(ascii_uppercase) for i in range(max_len))

        elif type in ["IntegerField", "PositiveIntegerField", "SmallIntegerField"]:
            value = sequence

        elif type in ["BooleanField"]:
            value = True if sequence % 2 == 0 else False

        elif type in ["DateField"]:
            value = timezone.now().date()

        # TODO support JSONField

        if value is None:
            raise NotImplementedError(f"{type} is not implemented")
            # TODO
            # FileField
            # UUIDField

        bundle[snake_to_camel(field)] = value

    return bundle


def verify_model_interface(instance, api="api"):  # pragma: no cover
    """
    Ensure that any editable snake case field has a corresponding camel.

    Right now it's just dumb luck that they match, there's no way to test this
    until now.

    TODO adapt this to work with Serializer
    """
    if not hasattr(instance, f"{api}_update_fields"):
        warnings.warn(
            f"{instance.__class__.__name__} does not have a method for {api}_update_fields"
        )
        return True

    editable_fields = getattr(instance, f"{api}_update_fields")()

    interface = getattr(instance, api)().keys()

    for snake in editable_fields:
        assert hasattr(
            instance, snake
        ), f"{instance.__class__.__name__} does not have field {snake}"
        camel = snake_to_camel(snake)
        assert (
            camel in interface
        ), f"{camel} not present in {instance.__class__.__name__}.{api}"
