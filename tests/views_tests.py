from datetime import datetime, timedelta

from worf.serializers import deserialize


def test_profile_detail(client, db, profile, user):
    response = client.get(f"/profiles/{profile.pk}/")
    result = deserialize(response)
    assert response.status_code == 200, result
    assert result["username"] == user.username


def test_profile_list(client, db, profile, user):
    response = client.get("/profiles/")
    result = deserialize(response)
    assert response.status_code == 200, result
    assert len(result["profiles"]) == 1
    assert result["profiles"][0]["username"] == user.username


def test_profile_list_array_filter(client, db, profile_factory, tag_factory):
    tag1, tag2, tag3 = tag_factory.create_batch(3)
    profile_factory.create(tags=[tag1])
    profile_factory.create(tags=[tag2])
    profile_factory.create(tags=[tag1, tag2])
    profile_factory.create(tags=[tag3])
    profile_factory.create()
    response = client.get(f"/profiles/?tags={tag1.pk}&tags={tag2.pk}")
    result = deserialize(response)
    assert response.status_code == 200, result
    assert len(result["profiles"]) == 3


def test_profile_update_foreign_key(client, db, profile, role_factory, team_factory):
    role = role_factory.create()
    team = team_factory.create()

    url = f"/profiles/{profile.pk}/"

    payload = dict(role=role.pk, team=team.pk)
    response = client.patch(url, payload, content_type="application/json")
    result = deserialize(response)
    assert response.status_code == 200, result
    assert result["role"]["name"] == role.name
    assert result["team"]["name"] == team.name

    # invalid role
    response = client.patch(url, dict(role=123), content_type="application/json")
    result = deserialize(response)
    assert response.status_code == 422, result
    assert result["message"] == "Invalid role"

    # role is not nullable
    response = client.patch(url, dict(role=None), content_type="application/json")
    result = deserialize(response)
    assert response.status_code == 422, result
    assert result["message"] == "Invalid role"

    # team is nullable
    response = client.patch(url, dict(team=None), content_type="application/json")
    result = deserialize(response)
    assert response.status_code == 200, result
    assert result["team"] is None


def test_profile_update_many_to_many(client, db, profile, tag):
    url = f"/profiles/{profile.pk}/"

    response = client.patch(url, dict(tags=[tag.pk]), content_type="application/json")
    result = deserialize(response)
    assert response.status_code == 200, result
    assert len(result["tags"]) == 1
    assert result["tags"][0]["id"] == tag.pk
    assert result["tags"][0]["name"] == tag.name

    # tags can be empty
    response = client.patch(url, dict(tags=[]), content_type="application/json")
    result = deserialize(response)
    assert response.status_code == 200, result
    assert len(result["tags"]) == 0

    # tags is not nullable
    response = client.patch(url, dict(tags=None), content_type="application/json")
    result = deserialize(response)
    assert response.status_code == 422, result
    assert "tags accepts an array, got <class 'NoneType'> None" in result["message"]

    # tags must be pks.. for now anyway
    payload = dict(tags=["invalid"])
    response = client.patch(url, payload, content_type="application/json")
    result = deserialize(response)
    assert response.status_code == 422, result
    assert "tags accepts an array of integers" in result["message"]


def test_user_detail(client, db, user):
    response = client.get(f"/users/{user.pk}/")
    result = deserialize(response)
    assert response.status_code == 200, result
    assert result["username"] == user.username


def test_user_list(client, db, user):
    response = client.get("/users/")
    result = deserialize(response)
    assert response.status_code == 200, result
    assert len(result["users"]) == 1
    assert result["users"][0]["username"] == user.username


def test_user_list_filters(client, db, user_factory):
    january = datetime.fromisoformat("2021-01-01T00:00:00+00:00")
    february = datetime.fromisoformat("2021-02-01T00:00:00+00:00")
    march = datetime.fromisoformat("2021-03-01T00:00:00+00:00")

    user1 = user_factory.create(date_joined=january)
    user2 = user_factory.create(date_joined=february)
    user3 = user_factory.create(email="test3@test.com", date_joined=march)

    # search by email
    response = client.get(f"/users/?email={user1.email}")
    assert len(deserialize(response)["users"]) == 1

    # search by string
    response = client.get("/users/?q=example.com")
    assert len(deserialize(response)["users"]) == 2
    response = client.get(f"/users/?q={user3.email}")
    assert len(deserialize(response)["users"]) == 1

    # search by username -- filter ignored, username is not in filter_fields
    response = client.get(f"/users/?username={user2.username}")
    assert len(deserialize(response)["users"]) == 3

    # search by date joined
    response = client.get(
        "/users/?dateJoined__gte=2021-02-01T00:00:00Z&date_joined__lte=2021-02-15T00:00:00Z"
    )
    assert len(deserialize(response)["users"]) == 1
    assert deserialize(response)["users"][0]["username"] == user2.username


def test_user_list_sort_asc(client, db, user_factory):
    user_factory.create(username="a")
    user_factory.create(username="b")
    response = client.get("/users/?sort=id")
    result = deserialize(response)
    assert response.status_code == 200, result
    assert len(result["users"]) == 2
    assert result["users"][0]["username"] == "a"
    assert result["users"][1]["username"] == "b"


def test_user_list_sort_desc(client, db, user_factory):
    user_factory.create(username="a")
    user_factory.create(username="b")
    response = client.get("/users/?sort=-id")
    result = deserialize(response)
    assert response.status_code == 200, result
    assert len(result["users"]) == 2
    assert result["users"][0]["username"] == "b"
    assert result["users"][1]["username"] == "a"


def test_user_list_multisort(client, now, db, user_factory):
    user_factory.create(username="a", date_joined=now)
    user_factory.create(username="b", date_joined=now - timedelta(hours=1))
    user_factory.create(username="c", date_joined=now)
    user_factory.create(username="d", date_joined=now)
    response = client.get("/users/?sort=dateJoined&sort=-id")
    result = deserialize(response)
    assert response.status_code == 200, result
    assert len(result["users"]) == 4
    assert result["users"][0]["username"] == "b"
    assert result["users"][1]["username"] == "d"
    assert result["users"][2]["username"] == "c"
    assert result["users"][3]["username"] == "a"


def test_user_update(client, db, user):
    url = f"/users/{user.pk}/"
    payload = dict(username="testtest", email="something@example.com")
    response = client.patch(url, payload, content_type="application/json")
    result = deserialize(response)
    assert response.status_code == 200, result
    assert result["username"] == "testtest"
    assert result["email"] == "something@example.com"
