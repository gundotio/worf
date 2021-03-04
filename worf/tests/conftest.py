import pytest

from django.conf import settings


def pytest_configure():
    """Initialize Django settings"""
    settings.configure(
        DEBUG=True,
    )
