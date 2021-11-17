from django.contrib.auth.models import User

import factory
from factory.django import DjangoModelFactory

from tests.models import Profile, Role, Skill, Tag, Team


class ProfileFactory(DjangoModelFactory):
    user = factory.SubFactory("tests.factories.UserFactory")
    role = factory.SubFactory("tests.factories.RoleFactory")
    team = None

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if create and extracted:
            self.tags.set(extracted)

    class Meta:
        model = Profile


class RoleFactory(DjangoModelFactory):
    name = factory.Sequence(lambda i: f"Role {i}")

    class Meta:
        model = Role


class SkillFactory(DjangoModelFactory):
    name = factory.Sequence(lambda i: f"Skill {i}")

    class Meta:
        model = Skill


class TagFactory(DjangoModelFactory):
    name = factory.Sequence(lambda i: f"Tag {i}")

    class Meta:
        model = Tag


class TeamFactory(DjangoModelFactory):
    name = factory.Sequence(lambda i: f"Team {i}")

    class Meta:
        model = Team


class UserFactory(DjangoModelFactory):
    username = factory.Sequence(lambda i: f"user-{i}")
    email = factory.Sequence(lambda i: f"user-{i}@example.com")
    first_name = "Boba"
    last_name = factory.Sequence(lambda i: f"Fett {i}")

    class Meta:
        model = User
