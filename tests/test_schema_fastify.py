"""Behavior and work-count checks for schema hot paths."""

import pytest
from flask import Flask
from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.orm.exc import DetachedInstanceError

from flarchitect.schemas import bases


class _ModelBase(DeclarativeBase):
    pass


class Record(_ModelBase):
    __tablename__ = "schema_fastify_record"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))


class RecordSchema(bases.AutoSchema):
    class Meta:
        model = Record


def test_normal_and_missing_attributes_do_not_read_detached_policy(monkeypatch):
    def unexpected_lookup(*args, **kwargs):
        pytest.fail("Normal attribute access must not read detached-object configuration")

    monkeypatch.setattr(bases, "get_config_or_model_meta", unexpected_lookup)
    schema = bases.Base()
    missing = object()

    assert schema.get_attribute({"name": "example"}, "name", missing) == "example"
    assert schema.get_attribute({}, "name", missing) is missing


@pytest.mark.parametrize("ignore_detached", [True, False])
def test_detached_attribute_preserves_policy(ignore_detached):
    class Detached:
        @property
        def name(self):
            raise DetachedInstanceError("Detached test record")

    app = Flask(__name__)
    app.config["API_SERIALIZATION_IGNORE_DETACHED"] = ignore_detached
    with app.test_request_context():
        schema = bases.Base()
        if ignore_detached:
            assert schema.get_attribute(Detached(), "name", object()) is None
        else:
            with pytest.raises(DetachedInstanceError, match="Detached test record"):
                schema.get_attribute(Detached(), "name", object())


@pytest.mark.parametrize(
    ("path", "serialization_type", "cache_enabled"),
    [("/records", "url", True), ("/records?page=1", "url", False), ("/records", "dynamic", False)],
)
def test_field_cache_bypass_skips_fingerprint_and_preserves_output(monkeypatch, path, serialization_type, cache_enabled):
    app = Flask(__name__)
    app.config.update(API_ADD_RELATIONS=False, API_SERIALIZATION_TYPE=serialization_type)
    monkeypatch.setattr(bases, "_SCHEMA_FIELD_CACHE", {})
    original_fingerprint = bases.AutoSchema._field_cache_config_fingerprint
    fingerprint_calls = []

    def fingerprint(schema):
        fingerprint_calls.append(schema)
        return original_fingerprint(schema)

    monkeypatch.setattr(bases.AutoSchema, "_field_cache_config_fingerprint", fingerprint)
    record = Record(id=1, name="example")
    with app.test_request_context(path):
        first = RecordSchema()
        second = RecordSchema()
        assert first.dump(record) == second.dump(record) == {"id": 1, "name": "example"}
        assert set(first.fields) == set(second.fields) == {"id", "name"}

    assert len(fingerprint_calls) == (2 if cache_enabled else 0)
    assert len(bases._SCHEMA_FIELD_CACHE) == (1 if cache_enabled else 0)
