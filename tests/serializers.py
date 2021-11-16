from worf.serializers import fields, Serializer


class UserSerializer(Serializer):
    last_login = fields.DateTime(dump_only=True)
    date_joined = fields.DateTime(dump_only=True)

    class Meta:
        fields = [
            "username",
            "last_login",
            "date_joined",
            "email",
        ]


class ProfileSerializer(Serializer):
    username = fields.Function(lambda obj: obj.user.username)
    email = fields.Function(lambda obj: obj.user.email)
    role = fields.Nested("RoleSerializer")
    skills = fields.Nested("RatedSkillSerializer", attribute="ratedskill_set", many=True)
    team = fields.Nested("TeamSerializer")
    tags = fields.Nested("TagSerializer", many=True)
    user = fields.Nested("UserSerializer")

    class Meta:
        fields = [
            "username",
            "avatar",
            "email",
            "phone",
            "role",
            "skills",
            "team",
            "tags",
            "user",
        ]


class RatedSkillSerializer(Serializer):
    id = fields.Function(lambda obj: obj.skill.id)
    name = fields.Function(lambda obj: obj.skill.name)

    class Meta:
        fields = ["id", "name", "rating"]


class RoleSerializer(Serializer):
    class Meta:
        fields = ["id", "name"]


class TagSerializer(Serializer):
    class Meta:
        fields = ["id", "name"]


class TeamSerializer(Serializer):
    class Meta:
        fields = ["id", "name"]
