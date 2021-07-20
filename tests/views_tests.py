from worf.testing import deserialize


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
