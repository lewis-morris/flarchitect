from marshmallow import Schema, fields

from flarchitect.utils.general import HTTP_OK, handle_result
from flarchitect.utils.responses import serialize_output_with_mallow


class ItemSchema(Schema):
    """Schema for testing serialisation."""

    id = fields.Int(required=True)


class TestSerializeOutputWithMallow:
    """Tests for the ``serialize_output_with_mallow`` helper."""

    def test_serialization_returns_dict(self):
        """Serialising data produces a dictionary with value and count."""
        data = {"id": 1}
        result = serialize_output_with_mallow(ItemSchema(), data)
        assert result["value"] == {"id": 1}
        assert result["count"] == 1

    def test_handle_result_processes_serialized_output(self):
        """``handle_result`` correctly interprets serialised dictionaries."""
        data = {"id": 1}
        result = serialize_output_with_mallow(ItemSchema(), data)
        status, value, count, next_url, previous_url = handle_result(result)
        assert status == HTTP_OK
        assert value == {"id": 1}
        assert count == 1
        assert next_url is None
        assert previous_url is None
