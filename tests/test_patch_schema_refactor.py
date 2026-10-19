"""Preservation checks for PATCH schema preparation's module move."""

from types import SimpleNamespace

import pytest
from flask import Flask
from marshmallow import EXCLUDE, RAISE, Schema, ValidationError, fields

from flarchitect.schemas.patch import _prepare_patch_schema
from flarchitect.schemas.utils import deserialise_data
from flarchitect.specs.utils import _prepare_patch_schema as legacy_prepare_patch_schema


class ChildSchema(Schema):
    label = fields.String(required=True)


class ExampleSchema(Schema):
    name = fields.String(required=True, metadata={"description": "Name"})
    count = fields.Integer(required=True)
    child = fields.Nested(ChildSchema, required=True)
    tags = fields.List(fields.String(), required=True)
    output = fields.String(dump_only=True)

    class Meta:
        unknown = EXCLUDE


def test_legacy_import_is_same_function():
    assert legacy_prepare_patch_schema is _prepare_patch_schema
    assert _prepare_patch_schema(None) is None


@pytest.mark.parametrize("use_class", [False, True])
def test_patch_preserves_existing_class_and_instance_contract(use_class):
    source = ExampleSchema if use_class else ExampleSchema()
    patch = _prepare_patch_schema(source)
    assert type(patch).__name__ == ("PatchSchemaMeta" if use_class else "PatchExampleSchema")
    assert type(patch).__module__ == "abc"
    assert patch.unknown == (RAISE if use_class else EXCLUDE)
    assert all(not field.required and field.allow_none for field in patch.fields.values())
    assert patch.fields["output"].dump_only is True
    assert patch.fields["name"].metadata == {"description": "Name"}
    assert patch.load({}) == {}
    assert patch.load({"name": None, "tags": None}) == {"name": None, "tags": None}
    assert patch.load({"name": "A", "count": "2", "child": {"label": "B"}}) == {
        "name": "A", "count": 2, "child": {"label": "B"},
    }
    with pytest.raises(ValidationError) as error:
        patch.load({"count": "wrong", "child": {}})
    assert error.value.messages == {
        "count": ["Not a valid integer."], "child": {"label": ["Missing data for required field."]},
    }


def test_patch_copies_fields_and_does_not_mutate_original():
    original = ExampleSchema()
    patch = _prepare_patch_schema(original)
    another = _prepare_patch_schema(original)
    for name, field in original.fields.items():
        assert patch.fields[name] is not field
        assert patch.fields[name] is not another.fields[name]
    assert patch.fields["tags"].inner is not original.fields["tags"].inner
    assert patch.fields["child"].schema is not original.fields["child"].schema
    patch.fields["tags"].inner.required = True
    patch.fields["child"].schema.fields["label"].required = False
    assert original.fields["tags"].inner.required is False
    assert original.fields["child"].schema.fields["label"].required is True
    assert original.fields["name"].required is True
    assert original.fields["name"].allow_none is False
    with pytest.raises(ValidationError) as error:
        original.load({})
    assert set(error.value.messages) == {"name", "count", "child", "tags"}


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"name": None, "ignored": "value"}, {"name": None}),
        ({"count": "2", "child": "https://example.test/child/1"}, {"count": 2}),
        ({"count": "wrong"}, ({"count": ["Not a valid integer."]}, 400)),
    ],
)
def test_patch_deserialization_preserves_results(payload, expected):
    app = Flask(__name__)
    with app.test_request_context("/example/1", method="PATCH", json=payload):
        assert deserialise_data(ExampleSchema, SimpleNamespace(json=payload)) == expected
