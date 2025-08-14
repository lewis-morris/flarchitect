from marshmallow import Schema, fields

from flarchitect.specs.utils import get_openapi_meta_data


class DecimalSchema(Schema):
    """Schema with Decimal fields for metadata extraction tests."""

    value = fields.Decimal()
    value_with_format = fields.Decimal(metadata={"format": "decimal"})


def test_decimal_field_without_format():
    """Decimal field without explicit format returns only type information."""
    schema = DecimalSchema()
    meta = get_openapi_meta_data(schema.fields["value"])
    assert meta["type"] == "number"
    assert "format" not in meta


def test_decimal_field_with_format():
    """Decimal field with format metadata includes the format key."""
    schema = DecimalSchema()
    meta = get_openapi_meta_data(schema.fields["value_with_format"])
    assert meta["type"] == "number"
    assert meta["format"] == "decimal"
