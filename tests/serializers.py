from worf.serializers import Serializer


class UserSerializer(Serializer):
    def read(self, model):
        return dict(
            username=model.username,
            lastLogin=model.last_login,
            dateJoined=model.date_joined,
            email=model.email,
        )

    def write(self):
        return [
            "username",
            "email",
        ]


class ProfileSerializer(Serializer):
    def read(self, model):
        return dict(
            username=model.user.username,
            email=model.user.email,
            role=dict(name=model.role.name) if model.role else None,
            skills=[t.api() for t in model.ratedskill_set.all()],
            team=dict(name=model.team.name) if model.team else None,
            tags=[t.api() for t in model.tags.all()],
        )

    def write(self):
        return [
            "role",
            "skills",
            "team",
            "tags",
        ]
