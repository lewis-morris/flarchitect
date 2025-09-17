import pytest

from flarchitect.schemas.auth import LoginSchema


@pytest.mark.parametrize(
    "payload, field",
    [({"username": "ab", "password": "longenough"}, "username"), ({"username": "valid", "password": "123"}, "password")],
)
def test_login_schema_validations(payload, field):
    schema = LoginSchema()
    with pytest.raises(Exception) as exc:
        schema.load(payload)
    assert field in str(exc.value)

