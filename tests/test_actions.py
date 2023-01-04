from tests import parametrize


def test_action_model_func(user_client, profile):
    response = user_client.put(f"/profiles/{profile.pk}/unsubscribe/")
    result = response.json()
    assert response.status_code == 200, result
    profile.refresh_from_db()
    assert profile.is_subscribed is False
    assert profile.subscribed_at is None
    assert profile.subscribed_by is None


def test_action_model_func_with_user_argument(user_client, profile, user):
    response = user_client.put(f"/profiles/{profile.pk}/subscribe/")
    result = response.json()
    assert response.status_code == 200, result
    profile.refresh_from_db()
    assert profile.is_subscribed is True
    assert profile.subscribed_at is not None
    assert profile.subscribed_by == user


def test_action_view_func(user_client, profile, user):
    response = user_client.put(f"/profiles/{profile.pk}/resubscribe/")
    result = response.json()
    assert response.status_code == 200, result
    profile.refresh_from_db()
    assert profile.is_subscribed is True
    assert profile.subscribed_at is not None
    assert profile.subscribed_by == user


def test_invalid_action(user_client, profile):
    response = user_client.put(f"/profiles/{profile.pk}/invalid-action/")
    result = response.json()
    assert response.status_code == 400, result
    assert result["message"] == "Invalid action: invalid-action"


def test_invalid_arguments(user_client, profile):
    kwargs = dict(text="I love newsletters")
    response = user_client.put(f"/profiles/{profile.pk}/subscribe/", kwargs)
    result = response.json()
    assert response.status_code == 400, result
    assert result["message"].startswith("Invalid arguments:")
    assert result["message"].endswith("unexpected keyword argument 'text'")


@parametrize("method", ["GET", "DELETE", "PATCH", "POST"])
def test_invalid_method(user_client, method, profile):
    response = user_client.generic(method, f"/profiles/{profile.pk}/subscribe/")
    assert response.status_code == 405
