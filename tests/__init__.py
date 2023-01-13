from functools import wraps

import pytest
import pytest_factoryboy

fixture = pytest.fixture
raises = pytest.raises
register = pytest_factoryboy.register


@wraps(pytest.mark.kwparametrize)
def parametrize(*args, **kwargs):
    if not args:
        return pytest.mark.kwparametrize(kwargs)
    if isinstance(args[0], dict):
        return pytest.mark.kwparametrize(*args, **kwargs)
    if len(args) == 1 and not kwargs:
        return pytest.mark.kwparametrize(*args[0])
    return pytest.mark.parametrize(*args, **kwargs)
