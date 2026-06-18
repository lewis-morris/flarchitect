"""Tests for per-method authentication requirements and access policies."""

from types import SimpleNamespace

import pytest
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields
from sqlalchemy import Column, Integer, String
from sqlalchemy.pool import StaticPool

from flarchitect import Architect
from flarchitect.authentication.user import set_current_user

db = SQLAlchemy()


class ThingSchema(Schema):
    """Simple schema used for manual responses in tests."""

    status = fields.String()


def make_manual_app():
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        FULL_AUTO=True,
        API_CREATE_DOCS=False,
        API_AUTHENTICATE_METHOD=["custom"],
        API_AUTH_REQUIREMENTS={"GET": False, "POST": True},
    )

    def custom_auth():
        token = request.headers.get("X-Auth")
        if token == "ok":
            set_current_user(SimpleNamespace(id=1))
            return True
        return False

    app.config["API_CUSTOM_AUTH"] = custom_auth
    architect = Architect()
    with app.app_context():
        architect.init_app(app, api_full_auto=False)

    @app.route("/manual", methods=["GET", "POST"])
    @architect.schema_constructor(output_schema=ThingSchema)
    def manual_route():
        return {"status": "ok"}

    return app


def test_auth_requirements_skip_get_enforce_post():
    app = make_manual_app()
    client = app.test_client()

    get_resp = client.get("/manual")
    assert get_resp.status_code == 200

    unauth_post = client.post("/manual")
    assert unauth_post.status_code == 401

    ok_post = client.post("/manual", headers={"X-Auth": "ok"})
    assert ok_post.status_code == 200


class BaseModel(db.Model):
    __abstract__ = True


class Thing(BaseModel):
    __tablename__ = "things"

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)

    class Meta:
        pass


@pytest.fixture()
def policy_app():
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_ENGINE_OPTIONS={"poolclass": StaticPool},
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        FULL_AUTO=True,
        API_CREATE_DOCS=False,
        API_AUTHENTICATE_METHOD=["custom"],
        API_BASE_MODEL=BaseModel,
        SECRET_KEY="test-secret",
    )

    class OwnerPolicy:
        def scope_query(self, query, *, user, model, many, **_):
            if user is None:
                return query.filter(False)
            if many:
                return query.filter(model.owner_id == user.id)
            return query

        def can_read(self, obj, *, user, **_):
            return user is not None and getattr(obj, "owner_id", None) == user.id

        def can_create(self, data, *, user, **_):
            return user is not None and data.get("owner_id") == user.id

        def can_update(self, obj, data, *, user, **_):
            return user is not None and getattr(obj, "owner_id", None) == user.id

        def can_delete(self, obj, *, user, **_):
            return user is not None and getattr(obj, "owner_id", None) == user.id

    def custom_auth():
        raw = request.headers.get("X-User")
        if not raw:
            return False
        set_current_user(SimpleNamespace(id=int(raw)))
        return True

    app.config["API_CUSTOM_AUTH"] = custom_auth
    app.config["API_ACCESS_POLICY"] = OwnerPolicy

    db.init_app(app)

    architect = Architect()
    with app.app_context():
        architect.init_app(
            app,
            api_full_auto=True,
            api_base_model=BaseModel,
            session=db.session,
        )
        assert Thing in BaseModel.__subclasses__()
        assert architect.api and architect.api.created_routes
        db.create_all()

        db.session.add_all(
            [
                Thing(owner_id=1, name="one"),
                Thing(owner_id=2, name="two"),
            ]
        )
        db.session.commit()

    routes = sorted(str(rule.rule) for rule in app.url_map.iter_rules())
    assert any(rule.startswith("/api") for rule in routes), routes

    return app


def test_access_policy_scopes_and_mutations(policy_app):
    client = policy_app.test_client()

    # Unauthenticated requests are rejected by auth layer.
    assert client.get("/api/things").status_code == 401

    resp_user1 = client.get("/api/things", headers={"X-User": "1"})
    assert resp_user1.status_code == 200
    assert len(resp_user1.json["value"]) == 1
    assert resp_user1.json["value"][0]["owner_id"] == 1

    resp_user2 = client.get("/api/things", headers={"X-User": "2"})
    assert resp_user2.status_code == 200
    assert len(resp_user2.json["value"]) == 1
    assert resp_user2.json["value"][0]["owner_id"] == 2

    own_detail = client.get("/api/things/1", headers={"X-User": "1"})
    assert own_detail.status_code == 200
    assert own_detail.json["value"]["name"] == "one"

    forbidden_detail = client.get("/api/things/2", headers={"X-User": "1"})
    assert forbidden_detail.status_code == 403

    create_ok = client.post(
        "/api/things",
        headers={"X-User": "1"},
        json={"owner_id": 1, "name": "extra"},
    )
    assert create_ok.status_code == 200
    assert create_ok.json["value"]["owner_id"] == 1

    create_denied = client.post(
        "/api/things",
        headers={"X-User": "2"},
        json={"owner_id": 1, "name": "mismatch"},
    )
    assert create_denied.status_code == 403

    update_ok = client.patch(
        "/api/things/1",
        headers={"X-User": "1"},
        json={"name": "updated"},
    )
    assert update_ok.status_code == 200
    assert update_ok.json["value"]["name"] == "updated"

    update_denied = client.patch(
        "/api/things/2",
        headers={"X-User": "1"},
        json={"name": "nope"},
    )
    assert update_denied.status_code == 403

    delete_denied = client.delete("/api/things/2", headers={"X-User": "1"})
    assert delete_denied.status_code == 403

    delete_ok = client.delete("/api/things/1", headers={"X-User": "1"})
    assert delete_ok.status_code == 200
