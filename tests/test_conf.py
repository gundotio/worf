from worf.conf import settings


def test_settings():
    assert settings.WORF_API_NAME == "Test API"
    assert settings.WORF_API_ROOT == "/api/"
    assert settings.WORF_BROWSABLE_API is True
    assert settings.WORF_DEBUG is False
