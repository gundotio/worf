import subprocess

from worf import __version__
from worf.casing import camel_to_snake


def field_list(value):
    return [
        ".".join(map(camel_to_snake, field.split("."))) for field in string_list(value)
    ]


def get_version():
    try:
        hash = (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
            .strip()
            .decode()
        )
        return f"{__version__}@{hash}"
    except:  # pragma: no cover # noqa E722 Dont crash for any reason whatsoever
        return __version__


def string_list(value):
    return value.split(",") if isinstance(value, str) else value
