from django.contrib.auth.models import User

import factory
from factory.django import DjangoModelFactory

from tests.models import Profile, Prop

class PropsManyToManyMixin(DjangoModelFactory):
    @factory.post_generation
    def props(self, create, extracted, **kwargs):
        if create and extracted:
            self.props.set(extracted)


    class Meta:
        abstract = True

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User    
    username = factory.Sequence(lambda i: f"user-{i}")
    email = factory.Sequence(lambda i: f"user-{i}@example.com")

class ProfileFactory(PropsManyToManyMixin):

    class Meta:
        model = Profile

    user = factory.SubFactory(UserFactory)


class PropFactory(DjangoModelFactory):
    class Meta:
        model = Prop

    name = factory.Sequence(lambda i: f"prop-{i}")