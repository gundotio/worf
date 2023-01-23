from worf.casing import camel_to_snake


def field_list(value, delimiter="."):
    return [
        delimiter.join(map(camel_to_snake, field.split(".")))
        for field in string_list(value)
    ]


def string_list(value):
    return value.split(",") if isinstance(value, str) else value
