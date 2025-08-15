"""Tests for role-based access decorators."""

from collections.abc import Generator
from types import SimpleNamespace

import pytest
from flask import Flask
from flask.testing import FlaskClient
from marshmallow import Schema, fields

from flarchitect import Architect
from flarchitect.authentication import require_roles
from flarchitect.authentication.user import set_current_user
from flarchitect.exceptions import CustomHTTPException
from flarchitect.specs.utils import handle_authorization
from flarchitect.utils.response_helpers import create_response


def test_require_roles_all() -> None:
    """The decorator blocks access when required roles are missing."""

    @require_roles("admin")
    def sample() -> str:
        return "ok"

    set_current_user(SimpleNamespace(roles=["admin"]))
    assert sample() == "ok"

    set_current_user(None)
    with pytest.raises(CustomHTTPException) as exc:
        sample()
    assert exc.value.status_code == 401
    assert exc.value.reason == "Authentication required"

    set_current_user(SimpleNamespace(roles=["user"]))
    with pytest.raises(CustomHTTPException) as exc:
        sample()
    assert exc.value.status_code == 403
    assert exc.value.reason == "Insufficient role"


@pytest.fixture()
def client_roles() -> Generator[FlaskClient, None, None]:
    """Create a Flask client with a route enforcing roles."""

    app = Flask(__name__)
    app.config.update(FULL_AUTO=False, API_CREATE_DOCS=False)

    with app.app_context():
        architect = Architect(app=app)
        holder = SimpleNamespace(user=None)

        class PingSchema(Schema):
            status = fields.Str()

        @app.before_request
        def load_user() -> None:
            set_current_user(holder.user)

        @app.errorhandler(CustomHTTPException)
        def handle_custom(exc: CustomHTTPException):
            return create_response(
                status=exc.status_code,
                errors={"error": exc.error, "reason": exc.reason},
            )

        @app.route("/protected")
        @architect.schema_constructor(output_schema=PingSchema, roles=("admin",))
        def protected() -> dict[str, str]:
            return {"status": "ok"}

        client = app.test_client()
        yield client, holder


def test_schema_constructor_applies_roles(
    client_roles: tuple[FlaskClient, SimpleNamespace],
) -> None:
    """Access is restricted based on user roles when configured."""

    client, holder = client_roles

    holder.user = SimpleNamespace(roles=["admin"])
    resp = client.get("/protected")
    assert resp.status_code == 200

    holder.user = None
    resp = client.get("/protected")
    assert resp.status_code == 401

    holder.user = SimpleNamespace(roles=["user"])
    resp = client.get("/protected")
    assert resp.status_code == 403


def test_openapi_documents_roles() -> None:
    """OpenAPI specification documents required roles."""

    spec_template = {"parameters": [], "responses": {"401": {"description": ""}}}

    @require_roles("admin", "editor")
    def view() -> None:  # pragma: no cover - simple callable
        pass

    handle_authorization(view, spec_template)

    assert spec_template["security"] == [{"bearerAuth": []}]
    assert "Roles required: admin, editor" in spec_template["responses"]["401"]["description"]


def test_require_roles_any() -> None:
    """Access granted when user has any matching role."""

    @require_roles("admin", "editor", any_of=True)
    def sample() -> str:
        return "ok"

    set_current_user(SimpleNamespace(roles=["editor"]))
    assert sample() == "ok"

    set_current_user(None)
    with pytest.raises(CustomHTTPException) as exc:
        sample()
    assert exc.value.status_code == 401
    assert exc.value.reason == "Authentication required"

    set_current_user(SimpleNamespace(roles=["user"]))
    with pytest.raises(CustomHTTPException) as exc:
        sample()
    assert exc.value.status_code == 403
    assert exc.value.reason == "Insufficient role"


def test_openapi_documents_roles_accepted() -> None:
    """OpenAPI specification documents accepted roles."""

    spec_template = {"parameters": [], "responses": {"401": {"description": ""}}}

    @require_roles("admin", "editor", any_of=True)
    def view() -> None:  # pragma: no cover - simple callable
        pass

    handle_authorization(view, spec_template)

    assert spec_template["security"] == [{"bearerAuth": []}]
    assert "Roles accepted: admin, editor" in spec_template["responses"]["401"]["description"]
