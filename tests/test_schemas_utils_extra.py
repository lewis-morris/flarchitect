from flask import Flask
from marshmallow import Schema, fields
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from flarchitect.schemas.utils import deserialise_data, filter_keys


class _Base(DeclarativeBase):
    pass


class M(_Base):
    __tablename__ = "m"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()


class NestedSchema(Schema):
    child = fields.Nested(Schema.from_dict({"id": fields.Int()}))
    items = fields.List(fields.Nested(Schema.from_dict({"id": fields.Int()})))
    name = fields.Str()


def test_filter_keys_model_and_schema_overlap():
    schema = NestedSchema()
    inputs = [
        {"id": 1, "name": "a", "unknown": 2},
        {"child": {"id": 1}, "extra": True},
    ]
    out = filter_keys(M, schema, inputs)
    # unknown/extra keys removed
    assert out[0] == {"id": 1, "name": "a"}
    assert out[1] == {"child": {"id": 1}}


def test_deserialise_data_ignores_string_for_nested_and_nonlist_for_list_nested():
    app = Flask(__name__)
    with app.app_context():
        with app.test_request_context("/", json={
            "child": "http://example/child/1",  # should be ignored (not dict)
            "items": {"id": 2},  # should be ignored (not list)
            "name": "ok",
        }):
            # minimal response stub carrying parsed JSON
            from types import SimpleNamespace

            resp = SimpleNamespace(json={
                "child": "http://example/child/1",
                "items": {"id": 2},
                "name": "ok",
            })
            out = deserialise_data(NestedSchema, resp)  # type: ignore[arg-type]
            assert out == {"name": "ok"}
