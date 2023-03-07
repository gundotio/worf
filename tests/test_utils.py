import marshmallow.utils

import worf.utils


def test_missing():
    assert worf.utils.missing == marshmallow.utils.missing
