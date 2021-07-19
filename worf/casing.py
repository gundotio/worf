import re
from worf.exceptions import NamingThingsError

lookup_keywords = [
    "exact",
    "iexact",
    "contains",
    "icontains",
    "in",
    "gt",
    "gte",
    "lt",
    "lte",
    "startswith",
    "istartswith",
    "endswith",
    "iendswith",
    "range",
    "date",
    "year",
    "iso_year",
    "month",
    "day",
    "week",
    "week_day",
    "quarter",
    "time",
    "hour",
    "minute",
    "second",
    "isnull",
    "regex",
    "iregex",
]


def snake_to_camel(snake):
    invalid_msg = f"{snake} is not valid snake case. "
    if snake.lower() != snake:
        raise NamingThingsError(invalid_msg + "It has capital letters!")

    components = snake.split("_")
    if not "".join(x for x in components).isalpha():
        raise NamingThingsError(invalid_msg + "It has special chars!")

    return components[0] + "".join(x.title() for x in components[1:])


def camel_to_snake(camel):
    if camel.lower() == camel:
        return camel

    invalid_msg = f"{camel} is not valid camel case. "
    if not clean_lookup_keywords(camel).isalpha():
        raise NamingThingsError(invalid_msg + "It has non alphabetical chars!")

    snake = ""
    last_was_upper = True
    for value in camel:
        if value.isupper():
            if last_was_upper:
                raise NamingThingsError(
                    invalid_msg + "It has multiple upper-case chars sequentially!"
                )
            snake += "_" + value.lower()
        else:
            snake += value

        last_was_upper = value.isupper()
    return snake


def whitespace_to_camel(string):
    pos = string.find(" ")
    if pos == -1:
        return string[:1].lower() + string[1:]

    new_string = string[:pos] + string[pos + 1 :].capitalize()
    return whitespace_to_camel(new_string)


def clean_lookup_keywords(string):
    return re.sub("__(" + "|".join(lookup_keywords) + ")$", "", string)
