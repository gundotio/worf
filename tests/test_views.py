from datetime import datetime, timedelta

json_type = "application/json"


def test_profile_detail(client, db, profile_url, user):
    response = client.get(profile_url)
    result = response.json()
    assert response.status_code == 200, result
    assert result["username"] == user.username


def test_profile_list(client, db, profile, user):
    response = client.get("/profiles/")
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["profiles"]) == 1
    assert result["profiles"][0]["username"] == user.username


def test_profile_list_search(client, db, profile, user):
    response = client.get(f"/profiles/?name={user.first_name} {user.last_name}")
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["profiles"]) == 1
    assert result["profiles"][0]["username"] == user.username


def test_profile_list_subset_search(client, db, profile, user):
    response = client.get(f"/profiles/subset/?name={user.first_name} {user.last_name}")
    result = response.json()
    assert response.status_code == 200, result


def test_profile_list_array_filter(client, db, profile_factory, tag_factory):
    tag1, tag2, tag3 = tag_factory.create_batch(3)
    profile_factory.create(tags=[tag1])
    profile_factory.create(tags=[tag2])
    profile_factory.create(tags=[tag1, tag2])
    profile_factory.create(tags=[tag3])
    profile_factory.create()
    response = client.get(f"/profiles/?tags={tag1.pk}&tags={tag2.pk}")
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["profiles"]) == 3


def test_profile_update_fk(client, db, profile_url, role, team):
    payload = dict(role=role.pk, team=team.pk)
    response = client.patch(profile_url, payload, content_type=json_type)
    result = response.json()
    assert response.status_code == 200, result
    assert result["role"]["name"] == role.name
    assert result["team"]["name"] == team.name


def test_profile_update_fk_invalid_role(client, db, profile_url, role, team):
    response = client.patch(profile_url, dict(role=123), content_type=json_type)
    result = response.json()
    assert response.status_code == 422, result
    assert result["message"] == "Invalid role"


def test_profile_update_fk_role_is_not_nullable(client, db, profile_url, role, team):
    response = client.patch(profile_url, dict(role=None), content_type=json_type)
    result = response.json()
    assert response.status_code == 422, result
    assert result["message"] == "Invalid role"


def test_profile_update_fk_team_is_nullable(client, db, profile_url, role, team):
    response = client.patch(profile_url, dict(team=None), content_type=json_type)
    result = response.json()
    assert response.status_code == 200, result
    assert result["team"] is None


def test_profile_update_m2m(client, db, profile_url, tag):
    response = client.patch(profile_url, dict(tags=[tag.pk]), content_type=json_type)
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["tags"]) == 1
    assert result["tags"][0]["id"] == tag.pk
    assert result["tags"][0]["name"] == tag.name


def test_profile_update_m2m_can_be_empty(client, db, profile_url, tag):
    response = client.patch(profile_url, dict(tags=[]), content_type=json_type)
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["tags"]) == 0


def test_profile_update_m2m_is_not_nullable(client, db, profile_url, tag):
    response = client.patch(profile_url, dict(tags=None), content_type=json_type)
    result = response.json()
    assert response.status_code == 422, result
    assert "tags accepts an array, got <class 'NoneType'> None" in result["message"]


def test_profile_update_m2m_must_be_pks(client, db, profile_url, tag):
    payload = dict(tags=["invalid"])
    response = client.patch(profile_url, payload, content_type=json_type)
    result = response.json()
    assert response.status_code == 422, result
    assert "Invalid tags" in result["message"]


def test_profile_update_m2m_through(client, db, profile_url, skill):
    payload = dict(skills=[dict(id=skill.pk, rating=4)])
    response = client.patch(profile_url, payload, content_type=json_type)
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["skills"]) == 1
    assert result["skills"][0]["id"] == skill.pk
    assert result["skills"][0]["name"] == skill.name
    assert result["skills"][0]["rating"] == 4


def test_profile_update_m2m_through_can_be_empty(client, db, profile_url, skill):
    response = client.patch(profile_url, dict(skills=[]), content_type=json_type)
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["skills"]) == 0


def test_profile_update_m2m_through_is_not_nullable(client, db, profile_url, skill):
    response = client.patch(profile_url, dict(skills=None), content_type=json_type)
    result = response.json()
    assert response.status_code == 422, result
    assert "skills accepts an array, got <class 'NoneType'> None" in result["message"]


def test_profile_update_m2m_through_must_be_dicts(client, db, profile_url, skill):
    payload = dict(skills=["invalid"])
    response = client.patch(profile_url, payload, content_type=json_type)
    result = response.json()
    assert response.status_code == 422, result
    assert "Invalid skills" == result["message"]


def test_profile_update_m2m_through_ids_must_be_pks(client, db, profile_url, skill):
    payload = dict(skills=[dict(id="invalid")])
    response = client.patch(profile_url, payload, content_type=json_type)
    result = response.json()
    assert response.status_code == 422, result
    assert "Invalid skills" in result["message"]


def test_profile_update_m2m_through_required_fields(client, db, profile_url, skill):
    payload = dict(skills=[dict(id=skill.pk)])
    response = client.patch(profile_url, payload, content_type=json_type)
    result = response.json()
    assert response.status_code == 422, result
    assert "Invalid skills" in result["message"]


def test_user_detail(client, db, user, user_url):
    response = client.get(user_url)
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
    january = datetime.fromisoformat("2021-01-01T00:00:00+00:00")
    february = datetime.fromisoformat("2021-02-01T00:00:00+00:00")
    march = datetime.fromisoformat("2021-03-01T00:00:00+00:00")

    user1 = user_factory.create(date_joined=january)
    user2 = user_factory.create(date_joined=february)
    user3 = user_factory.create(email="test3@test.com", date_joined=march)

    # search by email
    response = client.get(f"/users/?email={user1.email}")
    assert len(response.json()["users"]) == 1

    # search by string
    response = client.get("/users/?q=example.com")
    assert len(response.json()["users"]) == 2
    response = client.get(f"/users/?q={user3.email}")
    assert len(response.json()["users"]) == 1

    # search by username -- filter ignored, username is not in filter_fields
    response = client.get(f"/users/?username={user2.username}")
    assert len(response.json()["users"]) == 3

    # search by date joined
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
    response = client.get("/users/?sort=dateJoined&sort=-id")
    result = response.json()
    assert response.status_code == 200, result
    assert len(result["users"]) == 4
    assert result["users"][0]["username"] == "b"
    assert result["users"][1]["username"] == "d"
    assert result["users"][2]["username"] == "c"
    assert result["users"][3]["username"] == "a"


def test_user_update(client, db, user_url):
    payload = dict(username="testtest", email="something@example.com")
    response = client.patch(user_url, payload, content_type=json_type)
    result = response.json()
    assert response.status_code == 200, result
    assert result["username"] == "testtest"
    assert result["email"] == "something@example.com"
