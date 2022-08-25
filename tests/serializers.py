from worf.serializers import Serializer, fields


class UserSerializer(Serializer):
    last_login = fields.DateTime(dump_only=True)
    date_joined = fields.DateTime(dump_only=True)

    class Meta:
        fields = [
            "id",
            "username",
            "last_login",
            "date_joined",
            "email",
        ]


class ProfileSerializer(Serializer):
    username = fields.String(attribute="user.username")
    email = fields.String(attribute="user.email")
    avatar = fields.File(lambda profile: profile.get_avatar_url())
    role = fields.Nested("RoleSerializer")
    skills = fields.Nested("SkillSerializer", attribute="ratedskill_set", many=True)
    team = fields.Nested("TeamSerializer")
    tags = fields.Pluck("TagSerializer", "name", many=True)
    tasks = fields.Pluck("TaskSerializer", "name", many=True)
    user = fields.Nested("UserSerializer")

    class Meta:
        fields = [
            "id",
            "username",
            "email",
            "phone",
            "avatar",
            "boolean",
            "integer",
            "json",
            "positive_integer",
            "slug",
            "small_integer",
            "recovery_email",
            "resume",
            "role",
            "skills",
            "team",
            "tags",
            "tasks",
            "user",
            "last_active",
            "created_at",
        ]
        writable = [
            "id",
            "email",
            "phone",
            "avatar",
            "boolean",
            "integer",
            "json",
            "positive_integer",
            "slug",
            "small_integer",
            "recovery_email",
            "resume",
            "role",
            "skills",
            "team",
            "tags",
            "tasks",
            "user",
            "last_active",
            "created_at",
        ]


class RoleSerializer(Serializer):
    class Meta:
        fields = ["id", "name"]


class SkillSerializer(Serializer):
    id = fields.Integer(attribute="skill.id")
    name = fields.String(attribute="skill.name")

    class Meta:
        fields = ["id", "name", "rating"]


class TagSerializer(Serializer):
    class Meta:
        fields = ["id", "name"]


class TaskSerializer(Serializer):
    id = fields.UUID(attribute="custom_id")

    class Meta:
        fields = ["id", "name"]


class TeamSerializer(Serializer):
    class Meta:
        fields = ["id", "name"]
