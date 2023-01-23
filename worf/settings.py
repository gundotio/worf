from django.conf import settings

DATA_UPLOAD_MAX_MEMORY_SIZE = settings.DATA_UPLOAD_MAX_MEMORY_SIZE

WORF_API_NAME = getattr(settings, "WORF_API_NAME", "Worf API")
WORF_API_ROOT = getattr(settings, "WORF_API_ROOT", "/api/")

WORF_BROWSABLE_API = getattr(settings, "WORF_BROWSABLE_API", True)

WORF_DEBUG = getattr(settings, "WORF_DEBUG", settings.DEBUG)

WORF_SERIALIZER_DEFAULT_OPTIONS = getattr(
    settings, "WORF_SERIALIZER_DEFAULT_OPTIONS", {}
)
