from tests import parametrize
from worf import exceptions


@parametrize(
    dict(e=exceptions.ActionError("test")),
    dict(e=exceptions.AuthenticationError("test")),
    dict(e=exceptions.DataConflict("test")),
    dict(e=exceptions.FieldError("test")),
    dict(e=exceptions.NamingThingsError("test")),
    dict(e=exceptions.NotFound("test")),
    dict(e=exceptions.WorfError("test")),
)
def test_exception(e):
    assert e.message == str(e) == "test"
