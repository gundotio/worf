import unittest

from worf.casing import camel_to_snake, snake_to_camel
from worf.exceptions import NamingThingsError


class TestSnakeAndCamel(unittest.TestCase):
    def test_converts_to_camel(self):
        self.assertEqual(camel_to_snake("camelToSnake"), "camel_to_snake")

    def test_converts_to_snake(self):
        self.assertEqual(snake_to_camel("snake_to_camel"), "snakeToCamel")

    def test_camel_to_snake_raises_NamingThingsError(self):
        with self.assertRaises(NamingThingsError):
            camel_to_snake("Not_a_camel")

    def test_snake_to_camel_raises_NamingThingsError(self):
        with self.assertRaises(NamingThingsError):
            snake_to_camel("NotASnake")

    def test_camel_to_snake_catches_IDs(self):
        with self.assertRaises(NamingThingsError):
            camel_to_snake("thisIsNotAnValidID")

    def test_camel_to_snake_catches_invalid_chars(self):
        with self.assertRaises(NamingThingsError):
            camel_to_snake("thisAintNo🐪")

    def test_snake_to_camel_catches_invalid_chars(self):
        with self.assertRaises(NamingThingsError):
            snake_to_camel("this_aint_no_🐍")
