def test_browsable_api(client, db, profile, user):
    profile_url = f"/profiles/{profile.pk}/"
    response = client.get(profile_url, HTTP_ACCEPT="text/html,image/png")

    content = response.content.decode("UTF-8")

    assert response.status_code == 200, content
    assert "Test API" in content
    assert "/api/" in content
    assert "HTTP" in content
    assert "200" in content
    assert "Content-Type" in content
    assert "application/json" in content
    assert user.username in content

    assert client.get(profile_url, HTTP_ACCEPT="").json()
    assert client.get(profile_url, HTTP_ACCEPT="application/json").json()
    assert client.get(profile_url, HTTP_ACCEPT="text/plain").json()
    assert client.get(f"{profile_url}?format=json", HTTP_ACCEPT="text/html").json()
