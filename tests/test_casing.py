import pytest

from worf.casing import camel_to_snake, snake_to_camel
from worf.exceptions import NamingThingsError


def test_converts_to_camel():
    assert camel_to_snake("camelToSnake") == "camel_to_snake"


def test_converts_to_snake():
    assert snake_to_camel("snake_to_camel") == "snakeToCamel"


def test_camel_to_snake_raises_NamingThingsError():
    with pytest.raises(NamingThingsError):
        camel_to_snake("Not_a_camel")


def test_snake_to_camel_raises_NamingThingsError():
    with pytest.raises(NamingThingsError):
        snake_to_camel("NotASnake")


def test_camel_to_snake_returns_fast_for_lc():
    assert "snake" == camel_to_snake("snake")


def test_camel_to_snake_catches_IDs():
    with pytest.raises(NamingThingsError):
        camel_to_snake("thisIsNotAnValidID")


def test_camel_to_snake_catches_invalid_chars():
    with pytest.raises(NamingThingsError):
        camel_to_snake("thisAintNo🐪")


def test_snake_to_camel_catches_invalid_chars():
    with pytest.raises(NamingThingsError):
        snake_to_camel("this_aint_no_🐍")
