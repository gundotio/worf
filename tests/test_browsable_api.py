def test_browsable_api(client, db, profile, user):
    response = client.get(f"/profiles/{profile.pk}/", HTTP_ACCEPT="text/html,image/png")

    content = response.content.decode("UTF-8")

    assert response.status_code == 200, content
    assert "Test API" in content
    assert "/api/" in content
    assert "HTTP" in content
    assert "200" in content
    assert "Content-Type" in content
    assert "application/json" in content
    assert user.username in content

    assert client.get(f"/profiles/{profile.pk}/", HTTP_ACCEPT="").json()
    assert client.get(f"/profiles/{profile.pk}/", HTTP_ACCEPT="application/json").json()
    assert client.get(f"/profiles/{profile.pk}/", HTTP_ACCEPT="text/plain").json()
    assert client.get(f"/profiles/{profile.pk}/?format=json", HTTP_ACCEPT="text/html").json()
