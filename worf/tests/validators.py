from uuid import UUID
from django.test import TestCase

from worf.validators import ValidationMixin
from worf.exceptions import HTTP422


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
