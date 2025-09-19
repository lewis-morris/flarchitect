from __future__ import annotations

import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from flarchitect import Architect


class BaseModel(DeclarativeBase):
    """Lightweight base for aggregation fixtures."""


db = SQLAlchemy(model_class=BaseModel)


class Invoice(db.Model):
    """Invoice model providing a boolean flag for grouping."""

    __tablename__ = "invoices"

    class Meta:
        tag_group = "Billing"
        tag = "Invoice"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    total_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


@pytest.fixture()
def app() -> Flask:
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        API_TITLE="Aggregation API",
        API_VERSION="1.0",
        API_BASE_MODEL=db.Model,
        API_ALLOW_GROUPBY=True,
        API_ALLOW_AGGREGATION=True,
    )

    db.init_app(app)

    with app.app_context():
        db.create_all()
        db.session.add_all(
            [
                Invoice(paid=True, total_cents=1200),
                Invoice(paid=True, total_cents=3000),
                Invoice(paid=False, total_cents=5000),
            ]
        )
        db.session.commit()
        Architect(app)

    yield app


@pytest.fixture()
def client(app: Flask):
    return app.test_client()


def test_aggregation_label_keys_survive_response(client):
    response = client.get("/api/invoices?groupby=paid&id|invoice_count__count=1")
    assert response.status_code == 200

    payload = response.get_json()
    rows = payload["value"]

    assert isinstance(rows, list)
    assert rows, "expected aggregation rows"
    assert all("invoice_count" in row for row in rows)

    grouped = {bool(row["paid"]): row["invoice_count"] for row in rows}
    assert grouped.get(True) == 2
    assert grouped.get(False) == 1


def test_aggregation_invalid_column_reports_base_name(client):
    response = client.get("/api/invoices?groupby=paid&unknown|foo__count=1")
    assert response.status_code == 400

    errors = response.get_json()["errors"]
    if isinstance(errors, dict):
        assert "Invalid column name: unknown" in str(errors.get("error"))
    else:
        assert "Invalid column name: unknown" in str(errors)
