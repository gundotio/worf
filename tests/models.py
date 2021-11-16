from uuid import uuid4

from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)

    avatar = models.FileField(upload_to="avatars/", blank=True)
    email = models.CharField(max_length=64)
    phone = models.CharField(max_length=64)

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.ForeignKey("Role", on_delete=models.CASCADE)
    team = models.ForeignKey("Team", blank=True, null=True, on_delete=models.SET_NULL)
    skills = models.ManyToManyField("Skill", through="RatedSkill")
    tags = models.ManyToManyField("Tag")

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


class Skill(models.Model):
    name = models.CharField(max_length=200)


class RatedSkill(models.Model):
    class Meta:
        ordering = ["skill__name"]
        unique_together = ["profile", "skill"]

    RATING_CHOICES = [
        (5, "Excellent"),
        (4, "Great"),
        (3, "Average"),
        (2, "Poor"),
        (1, "Bad"),
    ]

    profile = models.ForeignKey("Profile", on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    skill = models.ForeignKey("Skill", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.skill.name}: {self.get_rating_display()}"


class Tag(models.Model):
    name = models.CharField(max_length=200)


class Team(models.Model):
    name = models.CharField(max_length=64)
