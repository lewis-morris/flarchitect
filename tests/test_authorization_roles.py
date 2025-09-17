from __future__ import annotations

from collections.abc import Generator
from types import SimpleNamespace

import pytest
from flask import Flask
from flask.testing import FlaskClient
from marshmallow import Schema, fields

from flarchitect import Architect
from flarchitect.authentication.user import set_current_user
from flarchitect.exceptions import CustomHTTPException
from flarchitect.utils.response_helpers import create_response


class PongSchema(Schema):
    status = fields.Str()


@pytest.fixture()
def client_roles_enriched() -> Generator[tuple[FlaskClient, SimpleNamespace], None, None]:
    """Flask app fixture with enriched role map and simple routes."""

    app = Flask(__name__)
    app.config.update(FULL_AUTO=False, API_CREATE_DOCS=False)
    # Default example role map
    app.config.update(
        API_ROLE_MAP={
            "GET": {"roles": ["viewer", "admin"], "any_of": True},
            "POST": ["editor", "admin"],
            "ALL": "admin",
        }
    )

    with app.app_context():
        architect = Architect(app=app)
        holder = SimpleNamespace(user=None)

        @app.before_request
        def load_user() -> None:  # pragma: no cover - simple context injector
            set_current_user(holder.user)

        @app.errorhandler(CustomHTTPException)
        def handle_custom(exc: CustomHTTPException):  # pragma: no cover - envelope normalisation
            return create_response(status=exc.status_code, errors={"error": exc.error, "reason": exc.reason})

        @app.route("/resource", methods=["GET"])  # GET endpoint
        @architect.schema_constructor(output_schema=PongSchema, roles=("admin",))
        def get_resource() -> dict[str, str]:
            return {"status": "ok"}

        @app.route("/resource", methods=["POST"])  # POST endpoint
        @architect.schema_constructor(output_schema=PongSchema, roles=("admin", "editor"))
        def post_resource() -> dict[str, str]:
            return {"status": "ok"}

        client = app.test_client()
        yield client, holder


def test_enriched_forbidden_payload_get_any_of(client_roles_enriched: tuple[FlaskClient, SimpleNamespace]) -> None:
    client, holder = client_roles_enriched

    holder.user = SimpleNamespace(roles=["member"])  # Missing viewer/admin
    resp = client.get("/resource")

    assert resp.status_code == 403
    body = resp.get_json()
    assert body["errors"]["error"] == "forbidden"
    assert body["errors"]["message"].lower().startswith("missing required role")
    assert body["errors"]["required_roles"] == ["viewer", "admin"]
    assert body["errors"]["any_of"] is True
    assert body["errors"]["method"] == "GET"
    assert body["errors"]["path"] == "/resource"
    assert body["errors"]["resolved_from"] == "GET"
    assert body["errors"]["reason"] == "missing_roles"


def test_enriched_forbidden_payload_post_all_of(client_roles_enriched: tuple[FlaskClient, SimpleNamespace]) -> None:
    client, holder = client_roles_enriched

    holder.user = SimpleNamespace(roles=["member"])  # Missing editor/admin
    resp = client.post("/resource")

    assert resp.status_code == 403
    body = resp.get_json()
    assert body["errors"]["required_roles"] == ["editor", "admin"]
    assert body["errors"]["any_of"] is False
    assert body["errors"]["resolved_from"] == "POST"


def test_unauthenticated_remains_401(client_roles_enriched: tuple[FlaskClient, SimpleNamespace]) -> None:
    client, holder = client_roles_enriched

    holder.user = None
    resp = client.get("/resource")
    assert resp.status_code == 401  # unchanged behaviour


def test_no_config_fallback_to_decorator_roles() -> None:
    """When API_ROLE_MAP is absent, fallback to decorator roles in payload."""

    app = Flask(__name__)
    app.config.update(FULL_AUTO=False, API_CREATE_DOCS=False)

    with app.app_context():
        architect = Architect(app=app)
        holder = SimpleNamespace(user=None)

        @app.before_request
        def load_user() -> None:  # pragma: no cover - simple context injector
            set_current_user(holder.user)

        @app.errorhandler(CustomHTTPException)
        def handle_custom(exc: CustomHTTPException):  # pragma: no cover - envelope normalisation
            return create_response(status=exc.status_code, errors={"error": exc.error, "reason": exc.reason})

        @app.route("/only")
        @architect.schema_constructor(output_schema=PongSchema, roles=("admin", "editor"))
        def only() -> dict[str, str]:
            return {"status": "ok"}

        client = app.test_client()

        holder.user = SimpleNamespace(roles=["member"])  # Missing both
        resp = client.get("/only")
        assert resp.status_code == 403
        body = resp.get_json()
        assert sorted(body["errors"]["required_roles"]) == ["admin", "editor"]
        assert body["errors"]["any_of"] is False
