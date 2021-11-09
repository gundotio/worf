from worf.exceptions import NamingThingsError


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

    if not camel.replace("__", "").isalpha():
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
