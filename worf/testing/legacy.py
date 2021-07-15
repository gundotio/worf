import json
import warnings

from random import choice
from string import ascii_uppercase

from django.utils import timezone

from worf.casing import camel_to_snake, snake_to_camel


def generate_endpoint_tests(TestCase, API, instance, uri, patch=False, overrides={}):
    """
    Generate tests against an API, instance and uri.

    @param API the API Class to be tested
    @param instance: the model instance (usually created in test setup)
    @param uri: the path to the endpoint
    @param patch: Optionally test patch
    @param overrides: Optionally override values in the bundle factory
    """

    # TODO - This only works wih the model method serialization.
    # if API.serializer is not None:

    bundle = {
        **bundle_factory(instance, f"{API.api_method}_update_fields", overrides),
        **overrides,
    }
    response = TestCase.client.get(uri)
    TestCase.assertEqual(response.status_code, 200)

    if patch is False:
        return

    response = TestCase.client.patch(uri, bundle, content_type="application/json")
    TestCase.assertEqual(
        "20",  # assert 200-ish
        str(response.status_code)[0:2],
        response.content.decode("UTF-8"),
    )
    assertion_factory(TestCase, instance, bundle, overrides)


def assertion_factory(TestCase, instance, bundle, overrides={}):
    """
    Automatically test that a django model matches bundle content.

    @param TestCase: A TestCase class instance, typically `self`
    @param instance: A model instance
    @param bundle: A dictionary, potentially created by bundle_factory
    """
    # TODO consider extending the django test client with these methods. 👇
    instance.refresh_from_db()
    for key in bundle.keys():
        field = camel_to_snake(key)

        if field in overrides:
            continue

        if instance._meta.get_field(field).get_internal_type() in ["ManyToManyField"]:
            result = [x.pk for x in getattr(instance, field).all()]
            TestCase.assertCountEqual(
                result,
                bundle[key],
                msg=f"M2M {key} not set. Bundle was: \n\n {bundle}. Instance saved: \n\n {result}",
            )
            continue

        result = getattr(instance, field)
        TestCase.assertEqual(
            result,
            bundle[key],
            msg=f"{key} not set. Bundle was: \n\n {bundle}. Instance saved: \n\n {result}",
        )


def bundle_factory(instance, serializer="api_update_fields", overrides={}):
    # TODO consider extending the django test client with these methods.
    # TODO handle Choices fields; otherwise we may pass invalid values
    """
    Return a valid python dictionary for api testing.

    @param instance the model instance we are testing against
    @param serializer (optional) the model method that sets update_fields

    Limitiations:
        - Does not generate nor include any FK's, 1:1's, M2M fields
        - Only sets up valid data. Should always 200
    """
    bundle = dict()

    sequence = 0
    for field in getattr(instance, serializer)():
        sequence += 1
        type = instance._meta.get_field(field).get_internal_type()

        if field in overrides:
            continue

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

        elif type in ["IntegerField", "PositiveIntergerField", "SmallIntegerField"]:
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


def deserialize(response):
    # TODO consider extending the django test client with these methods. 👆
    return json.loads(response.content.decode("UTF-8"))


def verify_model_interface(instance, api="api"):
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
