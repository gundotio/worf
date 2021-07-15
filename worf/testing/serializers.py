import warnings

from worf.casing import snake_to_camel


def verify_serializer_interface(Serializer, model, read_omit=[], write_omit=[]):
    """Ensure that any editable snake case field has a corresponding camel."""
    serializer = Serializer()

    if not hasattr(serializer, "write"):
        warnings.warn(f"{serializer.__class__.__name__} does not have a write() method")
        return True

    write_fields = getattr(serializer, "write")()

    read_fields = list(getattr(serializer, "read")(model))

    for snake in read_omit:
        camel = snake_to_camel(snake)
        if camel in read_fields:
            raise Exception(
                "{} is skipped from read by name, but exists in {}.read!".format(
                    snake, serializer.__class__.__name__
                )
            )
        read_fields.append(camel)

    for each in write_omit:
        if each not in write_fields:
            raise Exception(
                "{} is skipped from write by name, but doesn't exist in {}.write!".format(
                    each, serializer.__class__.__name__
                )
            )
        # write_fields.remove(each)

    for snake in write_fields:

        camel = snake_to_camel(snake)
        assert camel in read_fields, "{} not present in {}.read".format(
            camel, model.__class__.__name__
        )

        if snake in write_omit:
            continue
        assert hasattr(model, snake), "{} does not have field {}".format(
            model.__class__.__name__, snake
        )
