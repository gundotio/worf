import marshmallow

import tests.serializers
import worf.serializers


def test_missing():
    assert worf.serializers.missing == marshmallow.missing


def test_profile_serializer():
    assert f"{tests.serializers.ProfileSerializer()}"


def test_role_serializer():
    assert f"{tests.serializers.RoleSerializer()}"


def test_skill_serializer():
    assert f"{tests.serializers.SkillSerializer()}"


def test_tag_serializer():
    assert f"{tests.serializers.TagSerializer()}"


def test_task_serializer():
    assert f"{tests.serializers.TaskSerializer()}"


def test_team_serializer():
    assert f"{tests.serializers.TeamSerializer()}"


def test_user_serializer():
    assert f"{tests.serializers.UserSerializer()}"
