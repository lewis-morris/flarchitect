"""Soft delete integration tests."""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime

import pytest
from flask import Flask
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from flarchitect import Architect


class BaseModel(DeclarativeBase):
    """Base model providing audit fields and session access."""

    created: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


db = SQLAlchemy(model_class=BaseModel)


class Widget(db.Model):
    """Model with per-model soft delete configuration."""

    __tablename__ = "widgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)

    class Meta:
        soft_delete = True
        soft_delete_attribute = "deleted"
        soft_delete_values = (False, True)


class Gadget(db.Model):
    """Model relying on global soft delete configuration."""

    __tablename__ = "gadgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)

    class Meta:
        """Placeholder meta required for automatic route generation."""

        pass


@pytest.fixture()
def client_widget() -> Generator[FlaskClient, None, None]:
    """Client configured for the ``Widget`` model with Meta-based soft delete."""

    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        API_BASE_MODEL=db.Model,
        API_CREATE_DOCS=False,
        API_SOFT_DELETE=True,
        API_SOFT_DELETE_ATTRIBUTE="deleted",
        API_SOFT_DELETE_VALUES=(False, True),
    )
    db.init_app(app)
    with app.app_context():
        db.create_all()
        db.session.add(Widget(name="w1"))
        db.session.commit()
        Architect(app=app)
        yield app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client_gadget_soft() -> Generator[FlaskClient, None, None]:
    """Client with global soft delete enabled for the ``Gadget`` model."""

    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        API_BASE_MODEL=db.Model,
        API_CREATE_DOCS=False,
        API_ALLOW_FILTERS=False,
        API_SOFT_DELETE=True,
        API_SOFT_DELETE_ATTRIBUTE="deleted",
        API_SOFT_DELETE_VALUES=(False, True),
    )
    db.init_app(app)
    with app.app_context():
        db.create_all()
        db.session.add(Gadget(name="g1"))
        db.session.commit()
        Architect(app=app)
        yield app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client_gadget_hard() -> Generator[FlaskClient, None, None]:
    """Client with soft delete disabled for the ``Gadget`` model."""

    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        API_BASE_MODEL=db.Model,
        API_CREATE_DOCS=False,
        API_ALLOW_FILTERS=False,
        API_SOFT_DELETE=False,
    )
    db.init_app(app)
    with app.app_context():
        db.create_all()
        db.session.add(Gadget(name="g1"))
        db.session.commit()
        Architect(app=app)
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def test_soft_delete_marks_and_omits(client_widget: FlaskClient) -> None:
    """DELETE marks the ``deleted`` attribute and removes it from default queries."""

    delete_resp = client_widget.delete("/api/widgets/1")
    assert delete_resp.status_code == 200

    list_resp = client_widget.get("/api/widgets").json["value"]
    assert list_resp == []

    by_id = client_widget.get("/api/widgets/1")
    assert by_id.status_code == 404

    include_deleted = client_widget.get("/api/widgets/1?include_deleted=1").json["value"]
    assert include_deleted["deleted"] is True


def test_config_soft_delete_toggle(client_gadget_soft: FlaskClient, client_gadget_hard: FlaskClient) -> None:
    """Global configuration toggles soft delete behaviour."""

    soft_del = client_gadget_soft.delete("/api/gadgets/1")
    assert soft_del.status_code == 200
    soft_by_id = client_gadget_soft.get("/api/gadgets/1")
    assert soft_by_id.status_code == 404
    soft_included = client_gadget_soft.get("/api/gadgets/1?include_deleted=1").json["value"]
    assert soft_included["deleted"] is True

    hard_del = client_gadget_hard.delete("/api/gadgets/1")
    assert hard_del.status_code == 200
    hard_status = client_gadget_hard.get("/api/gadgets/1?include_deleted=1").status_code
    assert hard_status == 404
