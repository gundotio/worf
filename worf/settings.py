from django.conf import settings


WORF_API_NAME = getattr(settings, "WORF_API_NAME", "Worf API")
WORF_API_ROOT = getattr(settings, "WORF_API_ROOT", "/api/")

WORF_BROWSABLE_API = getattr(settings, "WORF_BROWSABLE_API", True)

WORF_DEBUG = getattr(settings, "WORF_DEBUG", settings.DEBUG)
