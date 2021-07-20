from datetime import datetime
from worf.serializers import deserialize


def test_user_detail(client, user):
    response = client.get(f"/users/{user.pk}/")
    assert response.status_code == 200
    assert deserialize(response)["username"] == "test"


def test_user_list(client, user):
    response = client.get(f"/users/")
    assert response.status_code == 200
    assert len(deserialize(response)["users"]) == 1
    assert deserialize(response)["users"][0]["username"] == "test"


def test_user_update(client, user):
    url = f"/users/{user.pk}/"
    bundle = dict(username="testtest", email="something@example.com")
    response = client.patch(url, bundle, content_type="application/json")
    assert response.status_code == 200
    assert deserialize(response)["username"] == "testtest"
    assert deserialize(response)["email"] == "something@example.com"


def test_user_search(client, django_user_model):
    django_user_model.objects.create(username="test", email="test@example.com", date_joined=datetime.fromisoformat("2021-01-01T00:00:00+00:00"))
    django_user_model.objects.create(username="test2", email="test2@example.com", date_joined=datetime.fromisoformat("2021-02-01T00:00:00+00:00"))
    django_user_model.objects.create(username="test3", email="test3@test.com", date_joined=datetime.fromisoformat("2021-03-01T00:00:00+00:00"))
    
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
    response = client.get(f"/users/?dateJoined__gte=2021-02-01T00:00:00Z&date_joined__lte=2021-02-15T00:00:00Z")
    assert len(deserialize(response)["users"]) == 1
    assert deserialize(response)["users"][0]["username"] == "test2"