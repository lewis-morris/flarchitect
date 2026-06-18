"""Tests for opting out of canonical route registration."""

from __future__ import annotations

from flask import Flask
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from flarchitect import Architect


def _make_app(config: dict | None = None) -> tuple[Flask, SQLAlchemy]:
    """Create an isolated Flask app and SQLAlchemy binding for tests."""

    app = Flask(__name__)
    base_config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "API_CREATE_DOCS": False,
        "FULL_AUTO": True,
        "API_REGISTER_CANONICAL_ROUTES": True,
    }
    if config:
        base_config.update(config)
    app.config.update(base_config)

    class BaseModel(DeclarativeBase):
        """Minimal base model providing session access for flarchitect."""


    db = SQLAlchemy(model_class=BaseModel)

    def _get_session(*_args, **_kwargs):
        return db.session

    BaseModel.get_session = staticmethod(_get_session)  # type: ignore[attr-defined]
    db.Model.get_session = staticmethod(_get_session)  # type: ignore[attr-defined]
    app.config["API_BASE_MODEL"] = db.Model

    db.init_app(app)
    return app, db


def _teardown(app: Flask, db: SQLAlchemy) -> None:
    """Drop all tables and dispose the session for the given app."""

    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_canonical_routes_enabled_by_default() -> None:
    app, db = _make_app()

    class Order(db.Model):  # type: ignore[valid-type]
        __tablename__ = "orders"

        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        description: Mapped[str] = mapped_column(String)

        class Meta:
            tag = "Order"

    try:
        with app.app_context():
            db.create_all()
            order = Order(description="auto")
            db.session.add(order)
            db.session.commit()
            order_id = order.id
            Architect(app=app)

        client = app.test_client()
        list_resp = client.get("/api/orders")
        assert list_resp.status_code == 200
        assert list_resp.get_json()["value"][0]["description"] == "auto"

        detail_resp = client.get(f"/api/orders/{order_id}")
        assert detail_resp.status_code == 200
        assert detail_resp.get_json()["value"]["description"] == "auto"
    finally:
        _teardown(app, db)


def test_global_flag_disables_canonical_routes_but_manual_handler_remains() -> None:
    app, db = _make_app({"API_REGISTER_CANONICAL_ROUTES": False})

    class Order(db.Model):  # type: ignore[valid-type]
        __tablename__ = "orders"

        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        description: Mapped[str] = mapped_column(String)

        class Meta:
            tag = "Order"

    @app.get("/api/orders")
    def manual_orders():
        return {"manual": True}

    try:
        with app.app_context():
            db.create_all()
            order = Order(description="manual")
            db.session.add(order)
            db.session.commit()
            order_id = order.id
            Architect(app=app)
            to_url = db.session.get(Order, order_id).to_url()

        client: FlaskClient = app.test_client()
        manual_resp = client.get("/api/orders")
        assert manual_resp.status_code == 200
        assert manual_resp.get_json() == {"manual": True}

        # Auto-generated detail route should not exist.
        assert client.get(f"/api/orders/{order_id}").status_code == 404

        # ``to_url`` still points to the canonical location so bespoke handlers can use it.
        assert to_url.endswith(f"/api/orders/{order_id}")
    finally:
        _teardown(app, db)


def test_meta_override_disables_canonical_for_specific_model() -> None:
    app, db = _make_app()

    class Order(db.Model):  # type: ignore[valid-type]
        __tablename__ = "orders"

        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        description: Mapped[str] = mapped_column(String)

        class Meta:
            tag = "Order"
            register_canonical_routes = False

    class Customer(db.Model):  # type: ignore[valid-type]
        __tablename__ = "customers"

        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        name: Mapped[str] = mapped_column(String)

        class Meta:
            tag = "Customer"

    try:
        with app.app_context():
            db.create_all()
            db.session.add_all([Order(description="first"), Customer(name="alice")])
            db.session.commit()
            Architect(app=app)

        client = app.test_client()
        # Canonical routes for Customer remain available.
        assert client.get("/api/customers").status_code == 200

        # Order canonical routes are suppressed.
        assert client.get("/api/orders").status_code == 404
    finally:
        _teardown(app, db)


def test_meta_endpoint_registered_when_canonical_disabled() -> None:
    app, db = _make_app()

    class Order(db.Model):  # type: ignore[valid-type]
        __tablename__ = "orders"

        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        description: Mapped[str] = mapped_column(String)

        class Meta:
            tag = "Order"
            endpoint = "orders/records"
            register_canonical_routes = False

    try:
        with app.app_context():
            db.create_all()
            order = Order(description="alt-endpoint")
            db.session.add(order)
            db.session.commit()
            order_id = order.id
            Architect(app=app)
            to_url = db.session.get(Order, order_id).to_url()

        client = app.test_client()
        # Canonical path stays free for bespoke handlers.
        assert client.get("/api/orders").status_code == 404

        list_resp = client.get("/api/orders/records")
        assert list_resp.status_code == 200
        assert list_resp.get_json()["value"][0]["description"] == "alt-endpoint"

        detail_resp = client.get(f"/api/orders/records/{order_id}")
        assert detail_resp.status_code == 200
        assert detail_resp.get_json()["value"]["description"] == "alt-endpoint"

        # ``to_url`` should align with the alternate endpoint.
        assert to_url.endswith(f"/api/orders/records/{order_id}")
    finally:
        _teardown(app, db)
