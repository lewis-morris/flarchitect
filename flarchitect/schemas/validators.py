import base64
import re
from collections.abc import Callable, Iterable
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation

import validators
from marshmallow import ValidationError
from validators import ValidationError as VE


def validate_datetime(value: str, formats: Iterable[str] | None = None) -> bool:
    """Validate a datetime string against multiple accepted formats.

    Args:
        value: The datetime string to validate.
        formats: Optional iterable of format strings to try when parsing ``value``.

    Returns:
        bool: ``True`` if ``value`` matches one of the provided formats.

    Raises:
        ValidationError: If ``value`` does not conform to any of the supplied formats.
    """

    if isinstance(value, datetime):
        return True

    # Add common formats with optional microseconds and Z for UTC
    formats = formats or [
        "%Y-%m-%d %H:%M:%S",  # Standard format
        "%Y-%m-%dT%H:%M:%S",  # ISO format without timezone
        "%Y-%m-%dT%H:%M:%S.%f",  # ISO format with microseconds
        "%Y-%m-%dT%H:%M:%S%z",  # ISO format with timezone offset
        "%Y-%m-%dT%H:%M:%S.%f%z",  # ISO format with microseconds and timezone
        "%Y-%m-%dT%H:%M:%SZ",  # ISO format with UTC (Z for zero-offset)
        "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO format with microseconds and UTC (Z)
    ]

    for datetime_format in formats:
        try:
            # Try to parse the datetime string using each format
            datetime.strptime(value, datetime_format)
            return True  # If parsing succeeds, the validation passes
        except ValueError:
            continue  # If parsing fails, try the next format

    # If none of the formats worked, raise a ValidationError
    raise ValidationError(f"Invalid datetime format. Acceptable formats are: {', '.join(formats)}")


def validate_date(value: str, formats: Iterable[str] | None = None) -> bool:
    """Validate that a string represents a date in one of the accepted formats.

    Args:
        value: The date string to validate.
        formats: Optional iterable of accepted date formats.

    Returns:
        bool: ``True`` if the string matches one of the accepted formats.

    Raises:
        ValidationError: If ``value`` cannot be parsed using any provided format.
    """

    if isinstance(value, date):
        return True

    formats = formats or ["%Y-%m-%d"]  # Default format is YYYY-MM-DD
    for date_format in formats:
        try:
            datetime.strptime(value, date_format)
            return True  # If one format works, the validation succeeds
        except ValueError:
            continue
    raise ValidationError(f"Invalid date format. Acceptable formats are: {', '.join(formats)}")


def validate_time(value: str, formats: Iterable[str] | None = None) -> bool:
    """Validate that a string represents a time in one of the accepted formats.

    Args:
        value: The time string to validate.
        formats: Optional iterable of accepted time formats.

    Returns:
        bool: ``True`` if the string matches one of the accepted formats.

    Raises:
        ValidationError: If ``value`` cannot be parsed using any provided format.
    """

    if isinstance(value, time | datetime):
        return True
    # Define common time formats
    formats = formats or [
        "%H:%M:%S",  # Standard time format
        "%H:%M:%S.%f",  # Time with microseconds
        "%H:%M:%S%z",  # Time with timezone offset
        "%H:%M:%S.%f%z",  # Time with microseconds and timezone offset
        "%H:%M:%SZ",  # Time with UTC (Z for zero-offset)
        "%H:%M:%S.%fZ",  # Time with microseconds and UTC
    ]

    for time_format in formats:
        try:
            # Try to parse the time string using each format
            datetime.strptime(value, time_format)
            return True  # If parsing succeeds, the validation passes
        except ValueError:
            continue  # If parsing fails, try the next format

    # If none of the formats worked, raise a ValidationError
    raise ValidationError(f"Invalid time format. Acceptable formats are: {', '.join(formats)}")


def validate_decimal(value: str | int | float | Decimal) -> bool:
    """Validate that the provided value can be converted to a :class:`Decimal`.

    Args:
        value: The value to validate.

    Returns:
        bool: ``True`` if ``value`` is a valid decimal representation.

    Raises:
        ValidationError: If ``value`` cannot be converted to ``Decimal``.
    """

    try:
        Decimal(value)
        return True
    except (ValueError, InvalidOperation) as err:  # type: ignore[name-defined]
        raise ValidationError("Invalid decimal number.") from err


def validate_boolean(value: bool | str) -> bool:
    """Validate that a value represents a boolean.

    Args:
        value: The value to validate. Accepts booleans or common string representations.

    Returns:
        bool: ``True`` if ``value`` can be interpreted as a boolean.

    Raises:
        ValidationError: If ``value`` cannot be interpreted as boolean.
    """

    # Define truthy and falsy values
    truthy_values = {True, "1", "true", "True", "yes", "Yes"}
    falsy_values = {False, "0", "false", "False", "no", "No"}

    # Check if the value is in truthy or falsy sets
    if value in truthy_values or value in falsy_values:
        return True

    # If the value is neither truthy nor falsy, raise a validation error
    raise ValidationError("Invalid boolean value. Accepted values are: True, False, 1, 0, 'true', 'false', 'yes', 'no'.")


def validate_phone_number(value: str) -> bool:
    """Validate that a string represents a phone number.

    Args:
        value: The phone number string to validate.

    Returns:
        bool: ``True`` if the value resembles a phone number.

    Raises:
        ValidationError: If ``value`` is not a valid phone number.
    """

    pattern = re.compile(r"^\+?[0-9\s\-().]{7,20}$")
    if pattern.fullmatch(value):
        return True
    raise ValidationError("Phone number is not valid.")


def validate_postal_code(value: str) -> bool:
    """Validate that a string represents a postal code.

    Args:
        value: The postal code string to validate.

    Returns:
        bool: ``True`` if the value matches common postal code patterns.

    Raises:
        ValidationError: If ``value`` is not a valid postal code.
    """

    pattern = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\s\-]{2,10}$")
    if pattern.fullmatch(value):
        return True
    raise ValidationError("Postal code is not valid.")


def wrap_validator(validator: Callable[[str], bool | VE], error_message: str = "Not a valid value.") -> Callable[[str], None]:
    """Wrap a Marshmallow validator to raise :class:`ValidationError` on failure.

    Args:
        validator: The validation function to execute.
        error_message: Error message to raise if validation fails.

    Returns:
        Callable[[str], None]: A function that validates a value or raises a
        ``ValidationError``.
    """

    def wrapper(value: str) -> None:
        try:
            # Call the Marshmallow validator
            out = validator(value)
            if isinstance(out, VE):
                raise ValidationError(error_message)
        except ValidationError as err:
            # Re-raise the error to match Marshmallow's default behaviour
            raise ValidationError(err.messages) from err

    return wrapper


def validate_base64(value: str) -> bool:
    """Validate that a string is valid Base64.

    Uses Python's ``base64`` module with strict validation.

    Raises ``ValidationError`` if decoding fails.
    """
    try:
        # validate=True ensures only valid base64 alphabet and correct padding
        base64.b64decode(value, validate=True)
        return True
    except Exception as err:  # ValueError, binascii.Error
        raise ValidationError("Base64 string is not valid.") from err


def validate_cron(value: str) -> bool:
    """Validate a simple 5-field cron expression.

    Accepts common forms like ``*``, numbers, ranges (``1-5``), steps (``*/5`` or ``1-10/2``), and lists (``1,2,3``).
    """
    parts = value.split()
    if len(parts) != 5:
        raise ValidationError("Cron expression is not valid.")

    field_re = re.compile(r"^(\*|\d+|\d+-\d+|\*/\d+|\d+-\d+/\d+|\d+(,\d+)*)$")
    for part in parts:
        if not field_re.fullmatch(part):
            raise ValidationError("Cron expression is not valid.")
    return True


_ISO_4217_CODES: set[str] = {
    # Common currencies (not exhaustive, just enough for tests and typical usage)
    "USD",
    "EUR",
    "GBP",
    "JPY",
    "AUD",
    "CAD",
    "CHF",
    "CNY",
    "SEK",
    "NZD",
    "MXN",
    "SGD",
    "HKD",
    "NOK",
    "KRW",
    "TRY",
    "RUB",
    "INR",
    "BRL",
    "ZAR",
}


def validate_currency(value: str) -> bool:
    """Validate a 3-letter ISO 4217 currency code.

    The set is intentionally curated (non-exhaustive) and excludes placeholders like ``XXX``.
    """
    if isinstance(value, str) and len(value) == 3 and value.isalpha() and value.isupper() and value in _ISO_4217_CODES:
        return True
    raise ValidationError("Currency code is not valid.")


def _validate_hex_hash(value: str, length: int, algo_name: str) -> bool:
    """Validate a hex-encoded hash string of a given length."""
    if isinstance(value, str) and re.fullmatch(rf"[0-9a-fA-F]{{{length}}}", value):
        return True
    raise ValidationError(f"{algo_name} hash is not valid.")


def validate_by_type(validator_type: str) -> Callable[[str], None] | None:
    """Return a validation function based on the type of validator.

    Args:
        validator_type: The type of validator to use.

    Returns:
        Callable | None: The validation function or ``None`` if not found.
    """

    validation_map: dict[str, Callable[[str], None]] = {
        "email": wrap_validator(validators.email, "Email address is not valid."),
        "url": wrap_validator(validators.url, "URL is not valid."),
        "ipv4": wrap_validator(validators.ipv4, "IPv4 address is not valid."),
        "ipv6": wrap_validator(validators.ipv6, "IPv6 address is not valid."),
        "mac": wrap_validator(validators.mac_address, "MAC address is not valid."),
        "hostname": wrap_validator(validators.hostname, "Hostname is not valid."),
        "iban": wrap_validator(validators.iban, "IBAN is not valid."),
        "cron": validate_cron,
        "base64": validate_base64,
        "slug": wrap_validator(validators.slug, "Slug is not valid."),
        "uuid": wrap_validator(validators.uuid, "UUID is not valid."),
        "card": wrap_validator(validators.card_number, "Card number is not valid."),
        "country_code": wrap_validator(validators.country_code, "Country code is not valid."),
        "domain": wrap_validator(validators.domain, "Domain is not valid."),
        "md5": lambda v: _validate_hex_hash(v, 32, "MD5"),
        "sha1": lambda v: _validate_hex_hash(v, 40, "SHA1"),
        "sha224": lambda v: _validate_hex_hash(v, 56, "SHA224"),
        "sha256": lambda v: _validate_hex_hash(v, 64, "SHA256"),
        "sha384": lambda v: _validate_hex_hash(v, 96, "SHA384"),
        "sha512": lambda v: _validate_hex_hash(v, 128, "SHA512"),
        "currency": validate_currency,
        "phone": validate_phone_number,
        "postal_code": validate_postal_code,
        "date": lambda value: validate_date(value, formats=["%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"]),
        "datetime": lambda value: validate_datetime(
            value,
            formats=["%Y-%m-%d %H:%M:%S", "%d-%m-%Y %H:%M:%S", "%Y-%m-%dT%H:%M:%S"],
        ),
        "time": validate_time,
        "boolean": validate_boolean,
        "decimal": validate_decimal,
    }
    return validation_map.get(validator_type)
