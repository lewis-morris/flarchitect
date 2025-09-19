"""Regression tests verifying API output types for diverse SQLAlchemy columns."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum

import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from marshmallow import fields
from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum as SAEnum,
    Float,
    Integer,
    JSON,
    LargeBinary,
    Numeric,
    SmallInteger,
    String,
    Time,
    UUID as SAUUID,
    func,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy_utils import EmailType

from flarchitect import Architect
from flarchitect.schemas.bases import EnumField
from flarchitect.schemas.utils import get_input_output_from_model_or_make


class BaseModel(DeclarativeBase):
    """Declarative base used for test models."""


db = SQLAlchemy(model_class=BaseModel)


class Status(Enum):
    """Sample status enum to exercise Enum mapping."""

    NEW = "new"
    ACTIVE = "active"


class MixedTypes(db.Model):
    """Model exposing a range of SQLAlchemy types for serialization tests."""

    __tablename__ = "mixed_types"

    class Meta:
        tag = "Mixed"
        tag_group = "Testing"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    int_value: Mapped[int] = mapped_column(Integer, nullable=False)
    smallint_value: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    bigint_value: Mapped[int] = mapped_column(BigInteger, nullable=False)
    float_value: Mapped[float] = mapped_column(Float, nullable=False)
    numeric_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    bool_value: Mapped[bool] = mapped_column(Boolean, nullable=False)
    date_value: Mapped[date] = mapped_column(Date, nullable=False)
    datetime_value: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    time_value: Mapped[time] = mapped_column(Time, nullable=False)
    json_value: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    uuid_value: Mapped[uuid.UUID] = mapped_column(SAUUID(as_uuid=True), nullable=False)
    enum_value: Mapped[Status] = mapped_column(SAEnum(Status), nullable=False)
    binary_value: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    email_value: Mapped[str] = mapped_column(EmailType(), nullable=False)
    string_value: Mapped[str] = mapped_column(String, nullable=False)

    @hybrid_property
    def name_length(self) -> int:
        """Expose a hybrid property with a return annotation for field mapping."""

        return len(self.string_value or "")

    @name_length.expression
    def name_length(cls):  # type: ignore[override]
        return func.length(cls.string_value)


@pytest.fixture()
def app_with_mixed_types() -> tuple[Flask, int, dict[str, object]]:
    """Initialise a Flask app, register the model and seed a sample record."""

    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        API_TITLE="Type Matrix",
        API_VERSION="1.0",
        API_BASE_MODEL=db.Model,
        API_CREATE_DOCS=False,
        API_ENDPOINT_CASE="snake",
        API_FIELD_CASE="snake",
        FULL_AUTO=True,
    )

    db.init_app(app)

    with app.app_context():
        db.create_all()

        seeded = MixedTypes(
            int_value=7,
            smallint_value=9,
            bigint_value=2_147_483_648,
            float_value=3.1415,
            numeric_value=Decimal("99.95"),
            bool_value=True,
            date_value=date(2024, 1, 2),
            datetime_value=datetime(2024, 1, 2, 15, 30, 45),
            time_value=time(6, 45, 30),
            json_value={"labels": ["alpha", "beta"], "count": 2},
            uuid_value=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            enum_value=Status.ACTIVE,
            binary_value=b"hello-bytes",
            email_value="tester@example.com",
            string_value="sample text",
        )
        db.session.add(seeded)
        db.session.flush()

        expected_serialized = {
            "id": seeded.id,
            "int_value": seeded.int_value,
            "smallint_value": seeded.smallint_value,
            "bigint_value": seeded.bigint_value,
            "float_value": seeded.float_value,
            "numeric_value": str(seeded.numeric_value),
            "bool_value": seeded.bool_value,
            "date_value": seeded.date_value.isoformat(),
            "datetime_value": seeded.datetime_value.isoformat(),
            "time_value": seeded.time_value.isoformat(),
            "json_value": seeded.json_value,
            "uuid_value": str(seeded.uuid_value),
            "enum_value": seeded.enum_value.name,
            "binary_value": seeded.binary_value.decode(),
            "email_value": seeded.email_value,
            "string_value": seeded.string_value,
            "name_length": len(seeded.string_value),
        }

        record_id = seeded.id

        db.session.commit()

        Architect(app)

    return app, record_id, expected_serialized


def test_api_serialises_expected_python_types(app_with_mixed_types: tuple[Flask, int, dict[str, object]]) -> None:
    """Ensure API GET responses emit correctly typed payloads for each column."""

    app, record_id, expected = app_with_mixed_types
    client = app.test_client()

    response = client.get(f"/api/mixed_types/{record_id}")
    assert response.status_code == 200

    payload = response.get_json()["value"]

    assert payload["id"] == expected["id"]
    assert isinstance(payload["int_value"], int)
    assert isinstance(payload["smallint_value"], int)
    assert isinstance(payload["bigint_value"], int)
    assert isinstance(payload["float_value"], float)
    assert payload["numeric_value"] == expected["numeric_value"]
    assert isinstance(payload["bool_value"], bool)
    assert payload["date_value"] == expected["date_value"]
    assert payload["datetime_value"] == expected["datetime_value"]
    assert payload["time_value"] == expected["time_value"]
    assert payload["json_value"] == expected["json_value"]
    assert payload["uuid_value"] == expected["uuid_value"]
    assert payload["enum_value"] == expected["enum_value"]
    assert payload["binary_value"] == expected["binary_value"]
    assert payload["email_value"] == expected["email_value"]
    assert payload["string_value"] == expected["string_value"]
    assert payload["name_length"] == expected["name_length"]
    assert isinstance(payload["name_length"], int)


def test_auto_schema_field_mapping_matches_type_expectations(app_with_mixed_types: tuple[Flask, int, dict[str, object]]) -> None:
    """The generated AutoSchema should map SQLAlchemy types to the right fields."""

    app, _, _ = app_with_mixed_types

    with app.app_context():
        _input, output_schema = get_input_output_from_model_or_make(MixedTypes)
        schema_fields = output_schema.fields

        assert isinstance(schema_fields["int_value"], fields.Int)
        assert isinstance(schema_fields["smallint_value"], fields.Int)
        assert isinstance(schema_fields["bigint_value"], fields.Int)
        assert isinstance(schema_fields["float_value"], fields.Float)
        assert isinstance(schema_fields["numeric_value"], fields.Decimal)
        assert isinstance(schema_fields["bool_value"], fields.Bool)
        assert isinstance(schema_fields["date_value"], fields.Date)
        assert isinstance(schema_fields["datetime_value"], fields.DateTime)
        assert isinstance(schema_fields["time_value"], fields.Time)
        assert isinstance(schema_fields["json_value"], fields.Raw)
        assert isinstance(schema_fields["uuid_value"], fields.UUID)
        assert isinstance(schema_fields["enum_value"], EnumField)
        assert isinstance(schema_fields["binary_value"], fields.Str)
        assert isinstance(schema_fields["email_value"], fields.Email)
        assert isinstance(schema_fields["string_value"], fields.Str)
        assert isinstance(schema_fields["name_length"], fields.Int)
