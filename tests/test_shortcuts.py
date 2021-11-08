from worf.shortcuts import get_current_version


def test_get_current_version():
    assert get_current_version().startswith("v")
