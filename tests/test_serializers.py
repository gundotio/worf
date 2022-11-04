from tests.serializers import (
    ProfileSerializer,
    RoleSerializer,
    SkillSerializer,
    TagSerializer,
    TaskSerializer,
    TeamSerializer,
    UserSerializer,
)


def test_profile_serializer():
    assert f"{ProfileSerializer()}"


def test_role_serializer():
    assert f"{RoleSerializer()}"


def test_skill_serializer():
    assert f"{SkillSerializer()}"


def test_tag_serializer():
    assert f"{TagSerializer()}"


def test_task_serializer():
    assert f"{TaskSerializer()}"


def test_team_serializer():
    assert f"{TeamSerializer()}"


def test_user_serializer():
    assert f"{UserSerializer()}"
