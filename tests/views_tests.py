import pytest
from datetime import datetime, timedelta

from worf.serializers import deserialize

from tests.factories import ProfileFactory, TagFactory


def test_user_detail(client, user):
    response = client.get(f"/users/{user.pk}/")
    assert response.status_code == 200, deserialize(response)
    assert deserialize(response)["username"] == "test"


def test_user_list(client, user):
    response = client.get(f"/users/")
    assert response.status_code == 200, deserialize(response)
    assert len(deserialize(response)["users"]) == 1
    assert deserialize(response)["users"][0]["username"] == "test"


def test_user_list_filters(client, user_factory):
    user_factory.create(
        username="test",
        email="test@example.com",
        date_joined=datetime.fromisoformat("2021-01-01T00:00:00+00:00"),
    )
    user_factory.create(
        username="test2",
        email="test2@example.com",
        date_joined=datetime.fromisoformat("2021-02-01T00:00:00+00:00"),
    )
    user_factory.create(
        username="test3",
        email="test3@test.com",
        date_joined=datetime.fromisoformat("2021-03-01T00:00:00+00:00"),
    )

    # search by username -- filter ignored
    response = client.get(f"/users/?username=test2")
    assert len(deserialize(response)["users"]) == 3

    # search by email
    response = client.get(f"/users/?email=test@example.com")
    assert len(deserialize(response)["users"]) == 1

    # search string
    response = client.get(f"/users/?q=example.com")
    assert len(deserialize(response)["users"]) == 2

    # search by date joined
    response = client.get(
        f"/users/?dateJoined__gte=2021-02-01T00:00:00Z&date_joined__lte=2021-02-15T00:00:00Z"
    )
    assert len(deserialize(response)["users"]) == 1
    assert deserialize(response)["users"][0]["username"] == "test2"

@pytest.mark.django_db
def test_user_list_array_filter(client):
    tag1 = TagFactory.create()
    tag2 = TagFactory.create()
    tag3 = TagFactory.create()
    ProfileFactory.create(tags=[tag1])
    ProfileFactory.create(tags=[tag2])
    ProfileFactory.create(tags=[tag1,tag2])
    ProfileFactory.create(tags=[tag3])
    ProfileFactory.create()
    response = client.get(
        f"/profiles/?tags={tag1.pk}&tags={tag2.pk}"
    )
    assert response.status_code == 200, deserialize(response)
    assert len(deserialize(response)["profiles"]) == 3


def test_user_list_sort_asc(client, user_factory):
    user_factory.create(username="a")
    user_factory.create(username="b")
    response = client.get(f"/users/?sort=id")
    assert response.status_code == 200, deserialize(response)
    assert len(deserialize(response)["users"]) == 2
    assert deserialize(response)["users"][0]["username"] == "a"
    assert deserialize(response)["users"][1]["username"] == "b"


def test_user_list_sort_desc(client, user_factory):
    user_factory.create(username="a")
    user_factory.create(username="b")
    response = client.get(f"/users/?sort=-id")
    assert response.status_code == 200, deserialize(response)
    assert len(deserialize(response)["users"]) == 2
    assert deserialize(response)["users"][0]["username"] == "b"
    assert deserialize(response)["users"][1]["username"] == "a"


def test_user_list_multisort(client, now, user_factory):
    user_factory.create(username="a", date_joined=now)
    user_factory.create(username="b", date_joined=now - timedelta(hours=1))
    user_factory.create(username="c", date_joined=now)
    user_factory.create(username="d", date_joined=now)
    response = client.get(f"/users/?sort=dateJoined&sort=-id")
    assert response.status_code == 200, deserialize(response)
    assert len(deserialize(response)["users"]) == 4
    assert deserialize(response)["users"][0]["username"] == "b"
    assert deserialize(response)["users"][1]["username"] == "d"
    assert deserialize(response)["users"][2]["username"] == "c"
    assert deserialize(response)["users"][3]["username"] == "a"


def test_user_update(client, user):
    url = f"/users/{user.pk}/"
    bundle = dict(username="testtest", email="something@example.com")
    response = client.patch(url, bundle, content_type="application/json")
    assert response.status_code == 200, deserialize(response)
    assert deserialize(response)["username"] == "testtest"
    assert deserialize(response)["email"] == "something@example.com"
