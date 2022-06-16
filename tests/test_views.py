import pytest

from datetime import timedelta
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile


def test_profile_detail(client, db, profile, user):
    response = client.get(f"/profiles/{profile.pk}/")
    result = response.json()
    assert response.status_code == 200, result
    assert result["username"] == user.username


def test_profile_delete(client, db, profile, user):
    response = client.delete(f"/profiles/{profile.pk}/")
    assert response.status_code == 204, response.content
    assert response.content == b""


def test_profile_list(client, db, profile, user):
    response = client.get("/profiles/")
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["profiles"]) == 1
    assert result["profiles"][0]["username"] == user.username


def test_profile_list_filter(client, db, profile, user):
    response = client.get(f"/profiles/?name={user.first_name} {user.last_name}")
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["profiles"]) == 1
    assert result["profiles"][0]["username"] == user.username


def test_profile_list_icontains_filter(client, db, profile, user):
    response = client.get(f"/profiles/?name__icontains={user.first_name}")
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["profiles"]) == 1
    assert result["profiles"][0]["username"] == user.username


def test_profile_list_annotation_filter(client, db, profile_factory):
    profile_factory.create(user__date_joined="2020-01-01T00:00:00Z")
    profile_factory.create(user__date_joined="2020-12-01T00:00:00Z")
    response = client.get("/profiles/?dateJoined__gte=2020-06-01T00:00:00Z")
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["profiles"]) == 1


def test_profile_list_and_filter(client, db, profile_factory, tag_factory):
    tag1, tag2, tag3 = tag_factory.create_batch(3)
    profile_factory.create(tags=[tag1])
    profile_factory.create(tags=[tag2])
    profile_factory.create(tags=[tag1, tag2])
    profile_factory.create(tags=[tag3])
    profile_factory.create()
    response = client.get(f"/profiles/?tags={tag1.pk}&tags={tag2.pk}")
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["profiles"]) == 1


def test_profile_list_in_array_filter(client, db, profile, user):
    response = client.get(f"/profiles/?name__in={user.first_name} {user.last_name}&name__in=Din Djarin")
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["profiles"]) == 1
    assert result["profiles"][0]["username"] == user.username


def test_profile_list_in_string_filter(client, db, profile, user):
    response = client.get(f"/profiles/?name__in={user.first_name} {user.last_name},Din Djarin")
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["profiles"]) == 1
    assert result["profiles"][0]["username"] == user.username


def test_profile_list_or_filter(client, db, profile_factory, tag_factory):
    tag1, tag2, tag3 = tag_factory.create_batch(3)
    profile_factory.create(tags=[tag1])
    profile_factory.create(tags=[tag2])
    profile_factory.create(tags=[tag1, tag2])
    profile_factory.create(tags=[tag3])
    profile_factory.create()
    response = client.get(f"/profiles/?tags__in={tag1.pk}&tags__in={tag2.pk}")
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["profiles"]) == 3


def test_profile_list_negated_filter(client, db, profile, user):
    response = client.get(f"/profiles/?firstName!={user.first_name}")
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["profiles"]) == 0


def test_profile_list_negated__icontains__filter(client, db, profile, user):
    response = client.get(f"/profiles/?firstName__icontains!={user.first_name}")
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["profiles"]) == 0


def test_profile_list_not_in_array_filter(client, db, profile, user):
    response = client.get(f"/profiles/?name__in!={user.first_name} {user.last_name}&name__in!=Din Djarin")
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["profiles"]) == 0


def test_profile_list_not_in_string_filter(client, db, profile, user):
    response = client.get(f"/profiles/?name__in!={user.first_name} {user.last_name},Din Djarin")
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["profiles"]) == 0


def test_profile_list_subset_filter(client, db, profile, user):
    response = client.get(f"/profiles/subset/?name={user.first_name} {user.last_name}")
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["profiles"]) == 0


@patch('django.core.files.storage.FileSystemStorage.save')
def test_profile_multipart_create(mock_save, client, db, role, user):
    avatar = SimpleUploadedFile("avatar.jpg", b"", content_type="image/jpeg")
    mock_save.return_value = "avatar.jpg"
    payload = dict(avatar=avatar, role=role.pk, user=user.pk)
    response = client.post(f"/profiles/", payload)
    result = response.json()
    assert response.status_code == 201, result
    assert result["avatar"] == "/avatar.jpg"
    assert result["role"]["id"] == role.pk
    assert result["role"]["name"] == role.name
    assert result["user"]["username"] == user.username


@patch('django.core.files.storage.FileSystemStorage.save')
@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_profile_multipart_update(mock_save, client, db, method, profile, role, user):
    avatar = SimpleUploadedFile("avatar.jpg", b"", content_type="image/jpeg")
    mock_save.return_value = "avatar.jpg"
    payload = dict(avatar=avatar, role=role.pk, user=user.pk)
    response = client.generic(method, f"/profiles/{profile.pk}/", payload)
    result = response.json()
    assert response.status_code == 200, result
    assert result["avatar"] == "/avatar.jpg"
    assert result["role"]["id"] == role.pk
    assert result["role"]["name"] == role.name
    assert result["user"]["username"] == user.username


@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_profile_update_fk(client, db, method, profile, role, team):
    payload = dict(role=role.pk, team=team.pk)
    response = client.generic(method, f"/profiles/{profile.pk}/", payload)
    result = response.json()
    assert response.status_code == 200, result
    assert result["role"]["name"] == role.name
    assert result["team"]["name"] == team.name


@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_profile_update_fk_invalid_role(client, db, method, profile, role, team):
    response = client.generic(method, f"/profiles/{profile.pk}/", dict(role=123))
    result = response.json()
    assert response.status_code == 422, result
    assert result["message"] == "Invalid role"


@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_profile_update_fk_role_is_not_nullable(client, db, method, profile, role, team):
    response = client.generic(method, f"/profiles/{profile.pk}/", dict(role=None))
    result = response.json()
    assert response.status_code == 422, result
    assert result["message"] == "Invalid role"


@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_profile_update_fk_team_is_nullable(client, db, method, profile, role, team):
    response = client.generic(method, f"/profiles/{profile.pk}/", dict(team=None))
    result = response.json()
    assert response.status_code == 200, result
    assert result["team"] is None


@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_profile_update_m2m(client, db, method, profile, tag):
    response = client.generic(method, f"/profiles/{profile.pk}/", dict(tags=[tag.pk]))
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["tags"]) == 1
    assert result["tags"][0] == tag.name


@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_profile_update_m2m_can_be_empty(client, db, method, profile, tag):
    response = client.generic(method, f"/profiles/{profile.pk}/", dict(tags=[]))
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["tags"]) == 0


@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_profile_update_m2m_is_not_nullable(client, db, method, profile, tag):
    response = client.generic(method, f"/profiles/{profile.pk}/", dict(tags=None))
    result = response.json()
    assert response.status_code == 422, result
    assert "tags accepts an array, got <class 'NoneType'> None" in result["message"]


@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_profile_update_m2m_must_be_pks(client, db, method, profile, tag):
    payload = dict(tags=["invalid"])
    response = client.generic(method, f"/profiles/{profile.pk}/", payload)
    result = response.json()
    assert response.status_code == 422, result
    assert "Invalid tags" in result["message"]


@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_profile_update_m2m_through(client, db, method, profile, skill):
    payload = dict(skills=[dict(id=skill.pk, rating=4)])
    response = client.generic(method, f"/profiles/{profile.pk}/", payload)
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["skills"]) == 1
    assert result["skills"][0]["id"] == skill.pk
    assert result["skills"][0]["name"] == skill.name
    assert result["skills"][0]["rating"] == 4


@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_profile_update_m2m_through_can_be_empty(client, db, method, profile, skill):
    response = client.generic(method, f"/profiles/{profile.pk}/", dict(skills=[]))
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["skills"]) == 0


@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_profile_update_m2m_through_is_not_nullable(client, db, method, profile, skill):
    response = client.generic(method, f"/profiles/{profile.pk}/", dict(skills=None))
    result = response.json()
    assert response.status_code == 422, result
    assert "skills accepts an array, got <class 'NoneType'> None" in result["message"]


@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_profile_update_m2m_through_must_be_dicts(client, db, method, profile, skill):
    payload = dict(skills=["invalid"])
    response = client.generic(method, f"/profiles/{profile.pk}/", payload)
    result = response.json()
    assert response.status_code == 422, result
    assert "Invalid skills" == result["message"]


@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_profile_update_m2m_through_ids_must_be_pks(client, db, method, profile, skill):
    payload = dict(skills=[dict(id="invalid")])
    response = client.generic(method, f"/profiles/{profile.pk}/", payload)
    result = response.json()
    assert response.status_code == 422, result
    assert "Invalid skills" in result["message"]


@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_profile_update_m2m_through_required_fields(client, db, method, profile, skill):
    payload = dict(skills=[dict(id=skill.pk)])
    response = client.generic(method, f"/profiles/{profile.pk}/", payload)
    result = response.json()
    assert response.status_code == 422, result
    assert "Invalid skills" in result["message"]


def test_user_detail(client, db, user):
    response = client.get(f"/users/{user.pk}/")
    result = response.json()
    assert response.status_code == 200, result
    assert result["username"] == user.username


def test_user_list(client, db, user):
    response = client.get("/users/")
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["users"]) == 1
    assert result["users"][0]["username"] == user.username


def test_user_list_filters(client, db, user_factory):
    january = "2021-01-01T00:00:00Z"
    february = "2021-02-01T00:00:00Z"
    march = "2021-03-01T00:00:00Z"

    user1 = user_factory.create(date_joined=january)
    user2 = user_factory.create(date_joined=february)
    user3 = user_factory.create(email="test3@test.com", date_joined=march)

    # filter by email
    response = client.get(f"/users/?email={user1.email}")
    assert len(response.json()["users"]) == 1

    # filter by string
    response = client.get("/users/?q=example.com")
    assert len(response.json()["users"]) == 2
    response = client.get(f"/users/?q={user3.email}")
    assert len(response.json()["users"]) == 1

    # filter by username -- filter ignored, username is not in filter_fields
    response = client.get(f"/users/?username={user2.username}")
    assert len(response.json()["users"]) == 3

    # filter by date joined
    gte, lte = "2021-02-01T00:00:00Z", "2021-02-15T00:00:00Z"
    response = client.get(f"/users/?dateJoined__gte={gte}&date_joined__lte={lte}")
    assert len(response.json()["users"]) == 1
    assert response.json()["users"][0]["username"] == user2.username


def test_user_list_sort_asc(client, db, user_factory):
    user_factory.create(username="a")
    user_factory.create(username="b")
    response = client.get("/users/?sort=id")
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["users"]) == 2
    assert result["users"][0]["username"] == "a"
    assert result["users"][1]["username"] == "b"


def test_user_list_sort_desc(client, db, user_factory):
    user_factory.create(username="a")
    user_factory.create(username="b")
    response = client.get("/users/?sort=-id")
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["users"]) == 2
    assert result["users"][0]["username"] == "b"
    assert result["users"][1]["username"] == "a"


def test_user_list_multisort(client, now, db, user_factory):
    user_factory.create(username="a", date_joined=now)
    user_factory.create(username="b", date_joined=now - timedelta(hours=1))
    user_factory.create(username="c", date_joined=now)
    user_factory.create(username="d", date_joined=now)
    response = client.get("/users/?sort=dateJoined&sort=-id&sort=invalid")
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["users"]) == 4
    assert result["users"][0]["username"] == "b"
    assert result["users"][1]["username"] == "d"
    assert result["users"][2]["username"] == "c"
    assert result["users"][3]["username"] == "a"


def test_user_unique_create_with_existing_value(client, db, user, user_factory):
    user_factory.create(username="already_taken")
    payload = dict(username="already_taken")
    response = client.post("/users/", payload)
    result = response.json()
    assert response.status_code == 422, result
    assert result["message"] == "Field username must be unique"


@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_user_unique_update_with_current_value(client, db, method, user, user_factory):
    payload = dict(username=user.username)
    response = client.generic(method, f"/users/{user.pk}/", payload)
    result = response.json()
    assert response.status_code == 200, result
    assert result["username"] == user.username


@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_user_unique_update_with_existing_value(client, db, method, user, user_factory):
    user_factory.create(username="already_taken")
    payload = dict(username="already_taken")
    response = client.generic(method, f"/users/{user.pk}/", payload)
    result = response.json()
    assert response.status_code == 422, result
    assert result["message"] == "Field username must be unique"


@pytest.mark.parametrize("method", ["PATCH", "PUT"])
def test_user_update(client, db, method, user):
    payload = dict(username="testtest", email="something@example.com")
    response = client.generic(method, f"/users/{user.pk}/", payload)
    result = response.json()
    assert response.status_code == 200, result
    assert result["username"] == "testtest"
    assert result["email"] == "something@example.com"
