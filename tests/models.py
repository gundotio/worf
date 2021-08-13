from django.db import models
from django.contrib.auth.models import User


class DummyModel(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    email = models.CharField(max_length=64)
    phone = models.CharField(max_length=64)

    def api(self):
        return dict(id=self.id, email=self.email, phone=self.phone)

    def api_update_fields(self):
        return [
            "id",
            "email",
            "phone",
        ]


class Role(models.Model):
    name = models.CharField(max_length=64)


class Tag(models.Model):
    name = models.CharField(max_length=200)

    def api(self):
        return dict(
            id=self.pk,
            name=self.name,
        )


class Tag(models.Model):
    name = models.CharField(max_length=200)

    def api(self):
        return dict(
            id=self.pk,
            name=self.name,
        )


class Team(models.Model):
    name = models.CharField(max_length=64)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, blank=True, null=True, on_delete=models.SET_NULL)
    tags = models.ManyToManyField(Tag)
