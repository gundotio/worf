import random

import factory
from factory.django import DjangoModelFactory

from django.contrib.auth.models import User
from django.utils import timezone

from tests.models import Profile, RatedSkill, Role, Skill, Tag, Task, Team


def random_skill_name():
    skills = [
        "Python",
        "C++",
        "Bash",
        "Django",
        "Docker",
        "JavaScript",
        "Vue.js",
    ]
    return random.choice(skills)


class ProfileFactory(DjangoModelFactory):
    user = factory.SubFactory("tests.factories.UserFactory")
    role = factory.SubFactory("tests.factories.RoleFactory")
    team = None
    phone = factory.Sequence(lambda i: f"555-{i}-5555")

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if create and extracted:
            self.tags.set(extracted)

    class Meta:
        model = Profile


class RatedSkillFactory(DjangoModelFactory):
    profile = factory.SubFactory("tests.factories.ProfileFactory")
    skill = factory.SubFactory("tests.factories.SkillFactory")
    rating = factory.LazyAttribute(lambda i: random.randrange(1, 6))

    class Meta:
        model = RatedSkill


class RoleFactory(DjangoModelFactory):
    name = factory.Sequence(lambda i: f"Role {i}")

    class Meta:
        model = Role


class SkillFactory(DjangoModelFactory):
    name = factory.Sequence(lambda i: f"{random_skill_name()} {i}")

    class Meta:
        model = Skill


class TagFactory(DjangoModelFactory):
    name = factory.Sequence(lambda i: f"Tag {i}")

    class Meta:
        model = Tag


class TaskFactory(DjangoModelFactory):
    name = factory.Sequence(lambda i: f"Task {i}")

    class Meta:
        model = Task


class TeamFactory(DjangoModelFactory):
    name = factory.Sequence(lambda i: f"Team {i}")

    class Meta:
        model = Team


class UserFactory(DjangoModelFactory):
    id = factory.Sequence(lambda i: i)
    username = factory.Sequence(lambda i: f"user-{i}")
    email = factory.Sequence(lambda i: f"user-{i}@example.com")
    first_name = "Boba"
    last_name = factory.Sequence(lambda i: f"Fett {i}")
    password = "Password123"
    last_login = timezone.now()

    class Meta:
        model = User
