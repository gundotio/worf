import pytest
import pytest_factoryboy

fixture = pytest.fixture
raises = pytest.raises
register = pytest_factoryboy.register


def parametrize(*args, **kwargs):
    if not args:
        return pytest.mark.kwparametrize(kwargs)
    if isinstance(args[0], dict):
        return pytest.mark.kwparametrize(*args, **kwargs)
    return pytest.mark.parametrize(*args, **kwargs)
