"""Unit tests for ``flarchitect.schemas.bases`` helpers."""

from __future__ import annotations

import enum
from typing import Any

import pytest
from flask import Flask
from marshmallow import ValidationError, fields
from sqlalchemy import Enum as SAEnum, ForeignKey, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property

from flarchitect.schemas.bases import AutoSchema, EnumField


class _Base(DeclarativeBase):
    """Lightweight SQLAlchemy base for schema tests."""


class ArticleStatus(enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class Author(_Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    articles: Mapped[list["Article"]] = relationship(back_populates="author")


class Article(_Base):
    __tablename__ = "article"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    status: Mapped[ArticleStatus] = mapped_column(SAEnum(ArticleStatus))
    author_id: Mapped[int] = mapped_column(ForeignKey("author.id"))
    author: Mapped[Author] = relationship(back_populates="articles")

    @hybrid_property
    def title_length(self) -> int:
        return len(self.title or "")

    @title_length.expression
    def title_length(cls) -> Any:  # pragma: no cover - SQL expression path
        return func.length(cls.title)


class ArticleSchema(AutoSchema):
    class Meta:
        model = Article


@pytest.fixture
def flask_app() -> Flask:
    app = Flask(__name__)
    app.config["TESTING"] = True
    return app


@pytest.fixture(autouse=True)
def reset_schema_caches(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("flarchitect.schemas.utils._SCHEMA_SUBCLASS_CACHE", {})
    monkeypatch.setattr("flarchitect.schemas.utils._DYNAMIC_SCHEMA_CACHE", {})


class Colour(enum.Enum):
    RED = "red"
    BLUE = "blue"


def test_enum_field_supported_modes_and_validation() -> None:
    field_by_key = EnumField(Colour)
    assert field_by_key._serialize(Colour.RED, "colour", object()) == "RED"
    assert field_by_key._deserialize("BLUE", "colour", {}) is Colour.BLUE

    field_by_value = EnumField(Colour, by_value=True)
    assert field_by_value._serialize(Colour.RED, "colour", object()) == "red"
    assert field_by_value._deserialize("red", "colour", {}) is Colour.RED

    with pytest.raises(ValidationError):
        field_by_key._serialize("red", "colour", object())

    with pytest.raises(ValidationError):
        field_by_key._deserialize("PURPLE", "colour", {})


def test_auto_schema_only_prunes_fields_and_preserves_context(flask_app: Flask) -> None:
    with flask_app.app_context():
        schema = ArticleSchema(only=["id", "title"], context={"marker": True})

    assert set(schema.fields) == {"id", "title"}
    assert set(schema.dump_fields) == {"id", "title"}
    assert set(schema.load_fields) == {"id", "title"}
    assert schema.context == {"marker": True, "current_depth": 0}


def test_generate_fields_covers_columns_relationships_and_hybrids(flask_app: Flask) -> None:
    with flask_app.app_context():
        schema = ArticleSchema()

    assert isinstance(schema.fields["id"], fields.Integer)
    assert isinstance(schema.fields["status"], EnumField)
    assert isinstance(schema.fields["author"], fields.Function)
    assert isinstance(schema.fields["author_id"], fields.Integer)
    assert isinstance(schema.fields["title_length"], fields.Int)
    assert schema.fields["title_length"].dump_only is True


class AnnotatedHybrid(_Base):
    __tablename__ = "annotated_hybrid"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    @hybrid_property
    def gross_total(self) -> float:
        return 123.45


class AnnotatedHybridSchema(AutoSchema):
    class Meta:
        model = AnnotatedHybrid


class UnannotatedHybrid(_Base):
    __tablename__ = "unannotated_hybrid"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    @hybrid_property
    def gross_total(self):  # intentionally missing annotation
        return 123.45


class UnannotatedHybridSchema(AutoSchema):
    class Meta:
        model = UnannotatedHybrid


def test_hybrid_property_uses_return_annotation(flask_app: Flask) -> None:
    with flask_app.app_context():
        schema = AnnotatedHybridSchema()

    assert isinstance(schema.fields["gross_total"], fields.Float)


def test_hybrid_property_without_annotation_defaults_to_string(flask_app: Flask) -> None:
    with flask_app.app_context():
        schema = UnannotatedHybridSchema()

    assert isinstance(schema.fields["gross_total"], fields.Str)


def test_hybrid_property_dump_preserves_numeric_type(flask_app: Flask) -> None:
    with flask_app.app_context():
        schema = AnnotatedHybridSchema()

        instance = AnnotatedHybrid()

        with flask_app.test_request_context("/"):
            payload = schema.dump(instance)

    assert isinstance(payload["gross_total"], float)
    assert payload["gross_total"] == pytest.approx(123.45)


@pytest.mark.parametrize(
    ("add_relations", "allow_join", "query", "expected_calls"),
    [
        (True, False, {}, 1),
        (False, False, {}, 0),
        (False, True, {"join": "author"}, 1),
        (False, True, {"join": "other"}, 0),
    ],
)
def test_handle_relationship_respects_flags(
    flask_app: Flask,
    monkeypatch: pytest.MonkeyPatch,
    add_relations: bool,
    allow_join: bool,
    query: dict[str, str],
    expected_calls: int,
) -> None:
    class RelationshipSchema(AutoSchema):
        class Meta:
            model = Article

        def generate_fields(self) -> None:  # pragma: no cover - bypass auto init
            return

    overrides = {"API_ADD_RELATIONS": add_relations, "API_ALLOW_JOIN": allow_join}

    def config_stub(key: str, *_, default=None, **__) -> Any:
        return overrides.get(key, default)

    monkeypatch.setattr("flarchitect.schemas.bases.get_config_or_model_meta", config_stub)

    calls: list[str] = []

    def track_call(self, attribute: str, *_args) -> None:
        calls.append(attribute)

    monkeypatch.setattr(RelationshipSchema, "add_relationship_field", track_call, raising=False)

    relationship_descriptor = Article.__mapper__.all_orm_descriptors["author"]

    with flask_app.app_context():
        schema = RelationshipSchema()
        with flask_app.test_request_context("/", query_string=query):
            schema._handle_relationship("author", "author", relationship_descriptor)

    assert len(calls) == expected_calls


def test_handle_relationship_respects_dump_relationships_query(
    flask_app: Flask, monkeypatch: pytest.MonkeyPatch
) -> None:
    class RelationshipSchema(AutoSchema):
        class Meta:
            model = Article

        def generate_fields(self) -> None:  # pragma: no cover - bypass auto init
            return

    monkeypatch.setattr(
        "flarchitect.schemas.bases.get_config_or_model_meta",
        lambda key, *_, default=None, **__: {"API_ADD_RELATIONS": True}.get(key, default),
    )

    calls: list[str] = []

    def track_call(self, attribute: str, *_args) -> None:
        calls.append(attribute)

    monkeypatch.setattr(RelationshipSchema, "add_relationship_field", track_call, raising=False)

    relationship_descriptor = Article.__mapper__.all_orm_descriptors["author"]

    with flask_app.app_context():
        schema = RelationshipSchema()
        with flask_app.test_request_context("/", query_string={"dump_relationships": "false"}):
            schema._handle_relationship("author", "author", relationship_descriptor)

    assert calls == []


def test_convert_case_handles_leading_underscores(flask_app: Flask) -> None:
    class CaseSchema(AutoSchema):
        class Meta:
            model = Article

        def generate_fields(self) -> None:  # pragma: no cover
            return

    flask_app.config["API_FIELD_CASE"] = "camel"

    with flask_app.app_context():
        schema = CaseSchema()
        assert schema._convert_case("_internal_value") == "internalValue"
        flask_app.config["API_IGNORE_UNDERSCORE_ATTRIBUTES"] = False
        assert schema._convert_case("_internal_value") == "_internalValue"
        flask_app.config["API_FIELD_CASE"] = "snake"
        assert schema._convert_case("mixedCaseField") == "mixed_case_field"


def test_post_dump_applies_configured_callback(flask_app: Flask) -> None:
    def callback(payload: dict, **_kw) -> dict:
        payload["injected"] = True
        return payload

    flask_app.config["API_DUMP_CALLBACK"] = callback

    with flask_app.app_context():
        schema = ArticleSchema(only=["id"])
        article = Article(title="Example", status=ArticleStatus.DRAFT)
        article.id = 42
        with flask_app.test_request_context("/", method="GET"):
            dumped = schema.dump(article)

    assert dumped == {"id": 42, "injected": True}
