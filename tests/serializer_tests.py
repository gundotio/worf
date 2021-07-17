from worf.serializers import deserialize


def test_user_get(client, django_user_model):
    user = django_user_model.objects.create_user(username="test", password="password")
    response = client.get("/user/{}/".format(user.pk))
    assert response.status_code == 200
    assert deserialize(response)["username"] == "test"

    bundle = dict(username="testtest", email="something@example.com")
    response = client.patch(
        "/user/{}/".format(user.pk), bundle, content_type="application/json"
    )
    assert response.status_code == 200
    assert deserialize(response)["username"] == "testtest"
    assert deserialize(response)["email"] == "something@example.com"
