from django.contrib.auth.models import User

import factory
from factory.django import DjangoModelFactory

from tests.models import Profile, Tag

class TagsManyToManyMixin(DjangoModelFactory):
    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if create and extracted:
            self.tags.set(extracted)


    class Meta:
        abstract = True

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User    
    username = factory.Sequence(lambda i: f"user-{i}")
    email = factory.Sequence(lambda i: f"user-{i}@example.com")

class ProfileFactory(TagsManyToManyMixin):

    class Meta:
        model = Profile

    user = factory.SubFactory(UserFactory)


class TagFactory(DjangoModelFactory):
    class Meta:
        model = Tag

    name = factory.Sequence(lambda i: f"tag-{i}")