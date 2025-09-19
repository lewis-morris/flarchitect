import pytest
from marshmallow import Schema, fields, ValidationError

from flarchitect.utils.responses import (
    serialise_output_with_mallow,
    serialize_output_with_mallow,
    check_serialise_method_and_return,
)


class ItemSchema(Schema):
    x = fields.Int(required=True)
    y = fields.Int(load_only=True, required=False)


class ExplodingSchema(Schema):
    def dump(self, obj, many=None):  # type: ignore[override]
        raise ValidationError({"x": ["bad value"]})


def test_serialise_output_with_mallow_list_and_pagination():
    schema = ItemSchema()
    data = {
        "query": [{"x": 1}, {"x": 2}],
        "next_url": "/next",
        "previous_url": "/prev",
    }
    out = serialise_output_with_mallow(schema, data)
    assert isinstance(out, dict)
    assert out["query"] == [{"x": 1}, {"x": 2}]
    # count inferred from list length when total_count not supplied
    assert out["total_count"] == 2
    assert out["next_url"] == "/next"
    assert out["previous_url"] == "/prev"


def test_serialise_output_with_mallow_dictionary_passthrough_for_extra_keys():
    schema = ItemSchema()
    data = {
        "dictionary": [{"x": 1, "extra": "value"}],
        "query": [{"x": 1, "extra": "value"}],
        "next_url": "/next",
    }
    out = serialise_output_with_mallow(schema, data)
    assert out["query"] == [{"x": 1, "extra": "value"}]
    assert out["total_count"] == 1
    assert out["next_url"] == "/next"
    assert out["previous_url"] is None


def test_serialise_output_with_mallow_reports_validation_errors_for_list_payload():
    schema = ItemSchema()
    data = {"query": [{"x": "not-an-int"}]}
    with pytest.raises(ValueError):
        serialise_output_with_mallow(schema, data)


def test_serialise_output_with_mallow_respects_explicit_total_count():
    schema = ItemSchema()
    data = {"query": [{"x": 1}], "total_count": 99, "previous_url": "/prev"}
    out = serialise_output_with_mallow(schema, data)
    assert out["total_count"] == 99
    assert out["previous_url"] == "/prev"


def test_serialise_output_with_mallow_uses_error_path():
    schema = ExplodingSchema()
    data = {"x": 1}
    out, status = serialise_output_with_mallow(schema, data)
    assert status == 500
    assert "errors" in out


def test_check_serialise_method_and_return_dictionary_passthrough():
    # Output should be returned directly when keys do not match schema/model
    result = {"dictionary": [{"a": 1, "b": 2}]}
    model_columns = ["id", "name"]
    schema_columns = ["id", "name"]
    schema = ItemSchema()
    out = check_serialise_method_and_return(result, schema, model_columns, schema_columns)
    assert out == [{"a": 1, "b": 2}]


def test_check_serialise_method_and_return_uses_schema_when_keys_match():
    result = {
        "dictionary": [{"x": 3}],
        "query": [{"x": 3}],
        "total_count": 5,
    }
    schema = ItemSchema()
    out = check_serialise_method_and_return(result, schema, model_columns=["x", "y"], schema_columns=["x", "y"])
    assert out["query"] == [{"x": 3}]
    assert out["total_count"] == 5
    assert "dictionary" not in result


def test_serialize_output_with_mallow_alias():
    schema = ItemSchema()
    data = {"x": 9}
    out = serialize_output_with_mallow(schema, data)
    assert out["query"] == {"x": 9}
    assert out["total_count"] == 1


def test_serialize_output_with_mallow_alias_list():
    schema = ItemSchema()
    data = [{"x": 1}, {"x": 2}]
    out = serialize_output_with_mallow(schema, data)
    assert out["query"] == [{"x": 1}, {"x": 2}]
    assert out["total_count"] == 2
