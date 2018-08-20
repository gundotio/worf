import unittest

from api.core.casing import camel_to_snake, snake_to_camel
from api.core.exceptions import NamingThingsError


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


from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, RequestFactory
from api.core.views import AbstractBaseAPI


class AbstractBaseAPITests(TestCase):
    def test_check_permissions(self):
        def dummy_perm(self, request):
            return 201

        class DummyAPI(AbstractBaseAPI):
            model = True
            permissions = [dummy_perm]

        inst = DummyAPI()
        inst.request = RequestFactory()
        with self.assertRaises(ImproperlyConfigured):
            inst._check_permissions()


from uuid import UUID
from django.core.exceptions import ValidationError
from django.db import models
from django.test import TestCase

from api.core.validators import ValidationMixin
from api.core.exceptions import HTTP422


class ValidationTests(TestCase):
    def setUp(self):
        self.obj = ValidationMixin()

    def test_validate_uuid_passes(self):
        string = "ce6a5b4f-599d-4442-8a74-d7a8d2b54854"
        result = self.obj.validate_uuid(string)
        self.assertEqual(result, UUID(string))

    def test_validate_uuid_raises_http422(self):
        string = "not-a-uuid"
        with self.assertRaises(HTTP422):
            self.obj.validate_uuid(string)

    def test_validate_email_passes(self):
        email = "something@example.com"
        result = self.obj.validate_email(email)
        self.assertEqual(email, result)

    def test_validate_email_raises_http422(self):
        email = "fake.example@com"
        with self.assertRaises(HTTP422):
            self.obj.validate_email(email)

    # def test_validate_skills_array(self):
    #     invalid = None
    #
    #     with self.assertRaises(ValidationError):
    #         invalid = self.obj.validate_skills_array(invalid)
    #
    #     valid_dict = dict(id=1, text='skill')
    #     skills = [
    #         dict(text='skill2'),
    #         valid_dict,
    #         True,
    #         0,
    #         [],
    #         None,
    #     ]
    #
    #     skills = self.obj.validate_skills_array(skills)
    #     self.assertEqual(skills, [valid_dict])
