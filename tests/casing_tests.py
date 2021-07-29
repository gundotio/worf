import pytest

from worf.casing import (
    camel_to_snake,
    clean_lookup_keywords,
    snake_to_camel,
    whitespace_to_camel,
)
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


def test_whitespace_to_camel():
    assert "thisIsAVerboseName" == whitespace_to_camel("This is a verbose name")


def test_clean_lookup_keywords():
    assert clean_lookup_keywords("name_with_keyword__gte") == "name_with_keyword"
    assert clean_lookup_keywords("name_with_keyword__contains") == "name_with_keyword"
    assert (
        clean_lookup_keywords("name_with_keyword__not_a_keyword")
        == "name_with_keyword__not_a_keyword"
    )
