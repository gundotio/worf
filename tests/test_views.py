from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile

from tests import parametrize


def test_profile_detail(client, db, profile, user):
    response = client.get(f"/profiles/{profile.pk}/")
    result = response.json()
    assert response.status_code == 200, result
    assert result["username"] == user.username


def test_profile_not_found(client, db, profile, user):
    response = client.get(f"/profiles/{uuid4()}/")
    result = response.json()
    assert response.status_code == 404, result
    assert result["message"] == "Not found"


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


@parametrize("page", [-1, 0, 1, 2])
def test_profile_list_pages(client, db, page):
    response = client.get("/profiles/", dict(page=page))
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["profiles"]) == 0


def test_profile_list_filters(client, db, profile, url, user):
    response = client.get(url("/profiles/", {"name": user.name}))
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["profiles"]) == 1
    assert result["profiles"][0]["username"] == user.username


@parametrize("url_params__array_format", ["repeat"])  # comma fails on ands
def test_profile_list_and_filters(client, db, profile_factory, tag_factory, url):
    tag1, tag2, tag3 = tag_factory.create_batch(3)
    profile_factory.create(tags=[tag1])
    profile_factory.create(tags=[tag2])
    profile_factory.create(tags=[tag1, tag2])
    profile_factory.create(tags=[tag3])
    profile_factory.create()
    response = client.get(url("/profiles/", {"tags": [tag1.pk, tag2.pk]}))
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["profiles"]) == 1


def test_profile_list_annotation_filters(client, db, profile_factory, url):
    profile_factory.create(user__date_joined="2020-01-01T00:00:00Z")
    profile_factory.create(user__date_joined="2020-12-01T00:00:00Z")
    filters = {"dateJoined__gte": "2020-06-01T00:00:00Z"}
    response = client.get(url("/profiles/", filters))
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["profiles"]) == 1


def test_profile_list_icontains_filters(client, db, profile, url, user):
    response = client.get(url("/profiles/", {"name__icontains": user.first_name}))
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["profiles"]) == 1
    assert result["profiles"][0]["username"] == user.username


@parametrize("url_params__array_format", ["comma", "repeat"])
def test_profile_list_in_filters(client, db, profile, url, user):
    response = client.get(url("/profiles/", {"name__in": [user.name, "Din Djarin"]}))
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["profiles"]) == 1
    assert result["profiles"][0]["username"] == user.username


@parametrize("include,expectation", [(["skills", "team"], True), ([], False)])
@parametrize("url_params__array_format", ["comma", "repeat"])
def test_profile_list_include(client, db, expectation, include, profile, url, user):
    response = client.get(url("/profiles/", {"include": include}))
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["profiles"]) == 1
    profile = result["profiles"][0]
    assert ("skills" in profile) is expectation
    assert ("team" in profile) is expectation


def test_profile_list_negated_filters(client, db, profile, url, user):
    response = client.get(url("/profiles/", {"firstName!": user.first_name}))
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["profiles"]) == 0


def test_profile_list_negated__icontains__filters(client, db, profile, url, user):
    response = client.get(url("/profiles/", {"firstName__icontains!": user.first_name}))
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["profiles"]) == 0


@parametrize("url_params__array_format", ["comma", "repeat"])
def test_profile_list_not_in_filters(client, db, profile, url, user):
    response = client.get(url("/profiles/", {"name__in!": [user.name, "Din Djarin"]}))
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["profiles"]) == 0


@parametrize("url_params__array_format", ["comma", "repeat"])
def test_profile_list_or_filters(client, db, profile_factory, tag_factory, url):
    tag1, tag2, tag3 = tag_factory.create_batch(3)
    profile_factory.create(tags=[tag1])
    profile_factory.create(tags=[tag2])
    profile_factory.create(tags=[tag1, tag2])
    profile_factory.create(tags=[tag3])
    profile_factory.create()
    response = client.get(url("/profiles/", {"tags__in": [tag1.pk, tag2.pk]}))
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["profiles"]) == 3


@patch("django.core.files.storage.FileSystemStorage.save")
def test_profile_multipart_create(mock_save, client, db, role, user):
    avatar = SimpleUploadedFile("avatar.jpg", b"", content_type="image/jpeg")
    mock_save.return_value = "avatar.jpg"
    payload = dict(avatar=avatar, role=role.pk, user=user.pk)
    response = client.post("/profiles/", payload)
    result = response.json()
    assert response.status_code == 201, result
    assert result["avatar"] == "/avatar.jpg"
    assert result["role"]["id"] == role.pk
    assert result["role"]["name"] == role.name
    assert result["user"]["username"] == user.username


@patch("django.core.files.storage.FileSystemStorage.save")
@parametrize("method", ["PATCH", "PUT"])
def test_profile_multipart_update(mock_save, client, db, method, profile, role, user):
    resume = SimpleUploadedFile("resume.pdf", b"", content_type="application/pdf")
    mock_save.return_value = "resume.pdf"
    payload = dict(resume=resume, role=role.pk, user=user.pk)
    response = client.generic(method, f"/profiles/{profile.pk}/", payload)
    result = response.json()
    assert response.status_code == 200, result
    assert result["resume"] == "/resume.pdf"
    assert result["role"]["id"] == role.pk
    assert result["role"]["name"] == role.name
    assert result["user"]["username"] == user.username


@parametrize("method", ["PATCH", "PUT"])
def test_profile_update_fk(client, db, method, profile, role, team):
    payload = dict(role=role.pk, team=team.pk)
    response = client.generic(method, f"/profiles/{profile.pk}/", payload)
    result = response.json()
    assert response.status_code == 200, result
    assert result["role"]["name"] == role.name
    assert result["team"]["name"] == team.name


@parametrize("method", ["PATCH", "PUT"])
def test_profile_update_fk_invalid_role(client, db, method, profile, role):
    response = client.generic(method, f"/profiles/{profile.pk}/", dict(role=123))
    result = response.json()
    assert response.status_code == 422, result
    assert result["message"] == "Invalid role"


@parametrize("method", ["PATCH", "PUT"])
def test_profile_update_fk_role_is_not_nullable(client, db, method, profile, role):
    response = client.generic(method, f"/profiles/{profile.pk}/", dict(role=None))
    result = response.json()
    assert response.status_code == 422, result
    assert result["message"] == "Invalid role"


@parametrize("method", ["PATCH", "PUT"])
def test_profile_update_fk_team_is_nullable(client, db, method, profile, role, team):
    response = client.generic(method, f"/profiles/{profile.pk}/", dict(team=None))
    result = response.json()
    assert response.status_code == 200, result
    assert result["team"] is None


@parametrize("method", ["PATCH", "PUT"])
def test_profile_update_m2m(client, db, method, profile, tag):
    response = client.generic(method, f"/profiles/{profile.pk}/", dict(tags=[tag.pk]))
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["tags"]) == 1
    assert result["tags"][0] == tag.name


@parametrize("method", ["PATCH", "PUT"])
def test_profile_update_m2m_can_be_empty(client, db, method, profile, tag):
    response = client.generic(method, f"/profiles/{profile.pk}/", dict(tags=[]))
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["tags"]) == 0


@parametrize("method", ["PATCH", "PUT"])
def test_profile_update_m2m_lookup_field(client, db, method, profile, task):
    payload = dict(tasks=[task.custom_id])
    response = client.generic(method, f"/profiles/{profile.pk}/", payload)
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["tasks"]) == 1
    assert result["tasks"][0] == task.name


@parametrize("method", ["PATCH", "PUT"])
def test_profile_update_m2m_is_not_nullable(client, db, method, profile, tag):
    response = client.generic(method, f"/profiles/{profile.pk}/", dict(tags=None))
    result = response.json()
    assert response.status_code == 422, result
    assert "tags accepts an array, got <class 'NoneType'> None" in result["message"]


@parametrize("method", ["PATCH", "PUT"])
def test_profile_update_m2m_must_be_pks(client, db, method, profile, tag):
    payload = dict(tags=["invalid"])
    response = client.generic(method, f"/profiles/{profile.pk}/", payload)
    result = response.json()
    assert response.status_code == 422, result
    assert "Invalid tags" in result["message"]


@parametrize("method", ["PATCH", "PUT"])
def test_profile_update_m2m_through(client, db, method, profile, skill):
    payload = dict(skills=[dict(id=skill.pk, rating=4)])
    response = client.generic(method, f"/profiles/{profile.pk}/", payload)
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["skills"]) == 1
    assert result["skills"][0]["id"] == skill.pk
    assert result["skills"][0]["name"] == skill.name
    assert result["skills"][0]["rating"] == 4


@parametrize("method", ["PATCH", "PUT"])
def test_profile_update_m2m_through_can_be_empty(client, db, method, profile, skill):
    response = client.generic(method, f"/profiles/{profile.pk}/", dict(skills=[]))
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["skills"]) == 0


@parametrize("method", ["PATCH", "PUT"])
def test_profile_update_m2m_through_is_not_nullable(client, db, method, profile, skill):
    response = client.generic(method, f"/profiles/{profile.pk}/", dict(skills=None))
    result = response.json()
    assert response.status_code == 422, result
    assert "skills accepts an array, got <class 'NoneType'> None" in result["message"]


@parametrize("method", ["PATCH", "PUT"])
def test_profile_update_m2m_through_must_be_dicts(client, db, method, profile, skill):
    payload = dict(skills=["invalid"])
    response = client.generic(method, f"/profiles/{profile.pk}/", payload)
    result = response.json()
    assert response.status_code == 422, result
    assert "Invalid skills" == result["message"]


@parametrize("method", ["PATCH", "PUT"])
def test_profile_update_m2m_through_ids_must_be_pks(client, db, method, profile, skill):
    payload = dict(skills=[dict(id="invalid")])
    response = client.generic(method, f"/profiles/{profile.pk}/", payload)
    result = response.json()
    assert response.status_code == 422, result
    assert "Invalid skills" in result["message"]


@parametrize("method", ["PATCH", "PUT"])
def test_profile_update_m2m_through_required_fields(client, db, method, profile, skill):
    payload = dict(skills=[dict(id=skill.pk)])
    response = client.generic(method, f"/profiles/{profile.pk}/", payload)
    result = response.json()
    assert response.status_code == 422, result
    assert "Invalid skills" in result["message"]


def test_staff_detail(admin_client, profile, user):
    response = admin_client.get(f"/staff/{profile.pk}/")
    result = response.json()
    assert response.status_code == 200, result
    assert result["username"] == user.username


def test_staff_detail_is_not_found_for_user(user_client, profile, user):
    response = user_client.get(f"/staff/{profile.pk}/")
    result = response.json()
    assert response.status_code == 404, result
    assert result["message"] == "Not found"


def test_staff_detail_is_unauthorized_for_guest(client, db, profile, user):
    response = client.get(f"/staff/{profile.pk}/")
    result = response.json()
    assert response.status_code == 401, result
    assert result["message"] == "Unauthorized"


def test_user_detail(client, db, user):
    response = client.get(f"/users/{user.pk}/")
    result = response.json()
    assert response.status_code == 200, result
    assert result["id"] == user.pk
    assert result["username"] == user.username


@parametrize("url_params__array_format", ["comma", "repeat"])
def test_user_detail_fields(client, db, url, user):
    response = client.get(url(f"/users/{user.pk}/", {"fields": ["id", "username"]}))
    result = response.json()
    assert response.status_code == 200, result
    assert result == dict(id=user.pk, username=user.username)


def test_user_list(client, db, user):
    response = client.get("/users/")
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["users"]) == 1
    assert result["users"][0]["id"] == user.pk
    assert result["users"][0]["username"] == user.username
    assert result["users"][0]["email"] == user.email


@parametrize("url_params__array_format", ["comma", "repeat"])
def test_user_list_fields(client, db, url, user):
    response = client.get(url("/users/", {"fields": ["id", "username"]}))
    result = response.json()
    assert response.status_code == 200, result
    assert result["users"] == [dict(id=user.pk, username=user.username)]
    response = client.get(url("/users/", {"fields": ["id", "name"]}))
    result = response.json()
    assert response.status_code == 400, result
    assert result == dict(message="Invalid fields: OrderedSet(['name'])")


@parametrize("url_params__array_format", ["comma", "repeat"])
def test_user_list_search(client, db, url, user):
    response = client.get(url("/users/", {"q": user.email}))
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["users"]) == 1
    response = client.get(url("/users/", {"q": user.email, "search": ["id"]}))
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["users"]) == 0
    response = client.get(url("/users/", {"q": user.email, "search": ["id", "email"]}))
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["users"]) == 1
    response = client.get(url("/users/", {"q": user.email, "search": ["id", "name"]}))
    result = response.json()
    assert response.status_code == 400, result
    assert result == dict(message="Invalid fields: {'name'}")


def test_user_list_filters(client, db, url, user_factory):
    january = "2021-01-01T00:00:00Z"
    february = "2021-02-01T00:00:00Z"
    march = "2021-03-01T00:00:00Z"

    user1 = user_factory.create(date_joined=january)
    user2 = user_factory.create(date_joined=february)
    user3 = user_factory.create(email="test3@test.com", date_joined=march)

    # filter by email
    response = client.get(url("/users/", {"email": user1.email}))
    assert len(response.json()["users"]) == 1

    # filter by string
    response = client.get(url("/users/", {"q": "example.com"}))
    assert len(response.json()["users"]) == 2
    response = client.get(url("/users/", {"q": user3.email}))
    assert len(response.json()["users"]) == 1

    # filter by username -- filter ignored, username is not in filter_fields
    response = client.get(url("/users/", {"username": user2.username}))
    assert len(response.json()["users"]) == 3

    # filter by date joined
    filters = {
        "dateJoined__gte": "2021-02-01T00:00:00Z",
        "dateJoined__lte": "2021-02-15T00:00:00Z",
    }
    response = client.get(url("/users/", filters))
    assert len(response.json()["users"]) == 1
    assert response.json()["users"][0]["username"] == user2.username


def test_user_list_sort_asc(client, db, url, user_factory):
    user_factory.create(username="a")
    user_factory.create(username="b")
    response = client.get(url("/users/", {"sort": "id"}))
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["users"]) == 2
    assert result["users"][0]["username"] == "a"
    assert result["users"][1]["username"] == "b"


def test_user_list_sort_desc(client, db, url, user_factory):
    user_factory.create(username="a")
    user_factory.create(username="b")
    response = client.get(url("/users/", {"sort": "-id"}))
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["users"]) == 2
    assert result["users"][0]["username"] == "b"
    assert result["users"][1]["username"] == "a"


@parametrize("url_params__array_format", ["comma", "repeat"])
def test_user_list_multisort(client, db, now, url, user_factory):
    date_joined = now()
    user_factory.create(username="a", date_joined=date_joined)
    user_factory.create(username="b", date_joined=date_joined - timedelta(hours=1))
    user_factory.create(username="c", date_joined=date_joined)
    user_factory.create(username="d", date_joined=date_joined)
    response = client.get(url("/users/", {"sort": ["dateJoined", "-id", "x"]}))
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["users"]) == 4
    assert result["users"][0]["username"] == "b"
    assert result["users"][1]["username"] == "d"
    assert result["users"][2]["username"] == "c"
    assert result["users"][3]["username"] == "a"


def test_user_self(client, user_client, user):
    response = client.get("/user/")
    assert response.status_code == 401

    response = user_client.get("/user/")
    assert response.status_code == 200


def test_user_unique_create_with_existing_value(client, db, user, user_factory):
    user_factory.create(username="already_taken")
    payload = dict(username="already_taken")
    response = client.post("/users/", payload)
    result = response.json()
    assert response.status_code == 422, result
    assert result["message"] == "Field username must be unique"


@parametrize("method", ["PATCH", "PUT"])
def test_user_unique_update_with_current_value(client, db, method, user, user_factory):
    payload = dict(username=user.username)
    response = client.generic(method, f"/users/{user.pk}/", payload)
    result = response.json()
    assert response.status_code == 200, result
    assert result["username"] == user.username


@parametrize("method", ["PATCH", "PUT"])
def test_user_unique_update_with_existing_value(client, db, method, user, user_factory):
    user_factory.create(username="already_taken")
    payload = dict(username="already_taken")
    response = client.generic(method, f"/users/{user.pk}/", payload)
    result = response.json()
    assert response.status_code == 422, result
    assert result["message"] == "Field username must be unique"


@parametrize("method", ["PATCH", "PUT"])
def test_user_update(client, db, method, user):
    payload = dict(username="testtest", email="something@example.com")
    response = client.generic(method, f"/users/{user.pk}/", payload)
    result = response.json()
    assert response.status_code == 200, result
    assert result["username"] == "testtest"
    assert result["email"] == "something@example.com"
