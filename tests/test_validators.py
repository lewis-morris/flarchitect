import uuid

import pytest
from marshmallow import ValidationError

from flarchitect.schemas.validators import (
    validate_boolean,
    validate_by_type,
    validate_date,
    validate_datetime,
    validate_decimal,
    validate_phone_number,
    validate_postal_code,
    validate_time,
)


@pytest.mark.parametrize(
    "validator,value",
    [
        (validate_datetime, "2024-01-01T12:00:00"),
        (validate_date, "2024-01-01"),
        (validate_time, "23:59:59"),
        (validate_decimal, "10.5"),
        (validate_boolean, "true"),
        (validate_phone_number, "+1 650-555-1234"),
        (validate_postal_code, "12345"),
    ],
)
def test_custom_validators_success(validator, value):
    """Custom validators accept expected values."""
    assert validator(value) is True


@pytest.mark.parametrize(
    "validator,value",
    [
        (validate_datetime, "2024/01/01 12:00:00"),
        (validate_date, "20240101"),
        (validate_time, "24:00:00"),
        (validate_decimal, "abc"),
        (validate_boolean, "maybe"),
        (validate_phone_number, "abc"),
        (validate_postal_code, "!!"),
    ],
)
def test_custom_validators_failure(validator, value):
    """Custom validators raise ``ValidationError`` for bad input."""
    with pytest.raises(ValidationError):
        validator(value)


@pytest.mark.parametrize(
    "vtype,valid,invalid",
    [
        ("email", "user@example.com", "not-email"),
        ("url", "https://example.com", "not-url"),
        ("ipv4", "192.168.1.1", "256.256.256.256"),
        ("ipv6", "2001:0db8:85a3:0000:0000:8a2e:0370:7334", "invalid"),
        ("mac", "00:1B:44:11:3A:B7", "invalid"),
        ("slug", "my-slug", "My Slug"),
        ("uuid", str(uuid.uuid4()), "not-uuid"),
        ("card", "4111111111111111", "1234"),
        ("country_code", "US", "XX"),
        ("domain", "example.com", "example"),
        ("md5", "d41d8cd98f00b204e9800998ecf8427e", "xyz"),
        ("sha1", "da39a3ee5e6b4b0d3255bfef95601890afd80709", "xyz"),
        ("sha224", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b", "xyz"),
        (
            "sha256",
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "xyz",
        ),
        ("sha384", "38b060a751ac96384cd9327eb1b1e36a21fdb71114be07434c0cc7bf63f6e1da274edebfe76f65fbd51ad2f14898b95b", "xyz"),
        (
            "sha512",
            "cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e",
            "xyz",
        ),
        ("hostname", "example.com", "invalid_host!"),
        ("iban", "GB82WEST12345698765432", "invalid"),
        ("cron", "* * * * *", "bad cron"),
        ("base64", "aGVsbG8=", "invalid"),
        ("currency", "USD", "XXX"),
        ("phone", "+1 650-555-1234", "not-phone"),
        ("postal_code", "12345", "!!!"),
        ("date", "2024-01-01", "20240101"),
        ("datetime", "2024-01-01 12:00:00", "2024/01/01 12:00:00"),
        ("time", "23:59:59", "24:00:00"),
        ("boolean", "true", "maybe"),
        ("decimal", "10.5", "abc"),
    ],
)
def test_validate_by_type(vtype, valid, invalid):
    """``validate_by_type`` returns a callable enforcing each type."""
    validator = validate_by_type(vtype)
    assert validator is not None
    validator(valid)
    with pytest.raises(ValidationError):
        validator(invalid)
