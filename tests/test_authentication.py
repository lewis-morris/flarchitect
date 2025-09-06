"""Authentication method integration tests."""

import base64
import datetime
from collections.abc import Generator

import jwt
import pytest
from flask import Flask, Response, request
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields
from sqlalchemy.pool import StaticPool
from werkzeug.security import check_password_hash, generate_password_hash

from flarchitect import Architect
from flarchitect.authentication.jwt import (
    decode_token,
    generate_access_token,
    generate_refresh_token,
    refresh_access_token,
)
from flarchitect.authentication.token_store import RefreshToken, get_refresh_token
from flarchitect.authentication.user import (
    current_user,
    get_current_user,
    set_current_user,
)
from flarchitect.exceptions import CustomHTTPException
from flarchitect.specs.generator import register_routes_with_spec
from flarchitect.utils.general import generate_readme_html
from flarchitect.utils.response_helpers import create_response

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True)
    password_hash = db.Column(db.String)
    api_key_hash = db.Column(db.String)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def check_api_key(self, key: str) -> bool:
        return check_password_hash(self.api_key_hash, key)


class UsernameSchema(Schema):
    """Schema for serializing responses containing a username."""

    username = fields.Str()


@pytest.fixture()
def client_basic() -> Generator[FlaskClient, None, None]:
    """Create a test client configured for basic authentication."""
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        FULL_AUTO=False,
        API_CREATE_DOCS=False,
        API_AUTHENTICATE_METHOD=["basic"],
        API_USER_MODEL=User,
        API_USER_LOOKUP_FIELD="username",
        API_CREDENTIAL_CHECK_METHOD="check_password",
    )
    db.init_app(app)
    with app.app_context():
        architect = Architect(app=app)
        architect.init_api(app=app, api_full_auto=False)
        architect.api.make_auth_routes()

        @app.errorhandler(CustomHTTPException)
        def handle_custom(exc: CustomHTTPException):
            return create_response(
                status=exc.status_code,
                errors={"error": exc.error, "reason": exc.reason},
            )

        @app.route("/basic")
        @architect.schema_constructor(model=User, output_schema=UsernameSchema)
        def basic_route() -> dict[str, str]:
            """Return the authenticated user's name for verification."""
            return {"username": current_user.username}

        db.create_all()
        user = User(
            username="alice",
            password_hash=generate_password_hash("wonderland"),
            api_key_hash=generate_password_hash("key"),
        )
        db.session.add(user)
        db.session.commit()
        yield app.test_client()


@pytest.fixture()
def client_api_key() -> Generator[FlaskClient, None, None]:
    """Create a test client configured for API key authentication."""
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        FULL_AUTO=False,
        API_CREATE_DOCS=False,
        API_AUTHENTICATE_METHOD=["api_key"],
        API_USER_MODEL=User,
        API_CREDENTIAL_HASH_FIELD="api_key_hash",
        API_CREDENTIAL_CHECK_METHOD="check_api_key",
        API_USER_LOOKUP_FIELD="username",
    )
    db.init_app(app)
    with app.app_context():
        architect = Architect(app=app)
        architect.init_api(app=app, api_full_auto=False)
        architect.api.make_auth_routes()

        @app.errorhandler(CustomHTTPException)
        def handle_custom(exc: CustomHTTPException):
            return create_response(
                status=exc.status_code,
                errors={"error": exc.error, "reason": exc.reason},
            )

        @app.route("/key")
        @architect.schema_constructor(model=User, output_schema=UsernameSchema)
        def key_route() -> dict[str, str]:
            """Return the authenticated user's name for verification."""
            return {"username": current_user.username}

        db.create_all()
        user = User(
            username="bob",
            password_hash=generate_password_hash("pw"),
            api_key_hash=generate_password_hash("secret"),
        )
        db.session.add(user)
        db.session.commit()
        yield app.test_client()


@pytest.fixture()
def client_jwt() -> Generator[tuple[FlaskClient, str, str], None, None]:
    """Create a test client configured for JWT authentication."""
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_ENGINE_OPTIONS={"poolclass": StaticPool},
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        FULL_AUTO=False,
        API_CREATE_DOCS=False,
        API_AUTHENTICATE_METHOD=["jwt"],
        API_USER_MODEL=User,
        API_USER_LOOKUP_FIELD="username",
        API_BASE_MODEL=User,
    )
    app.config["ACCESS_SECRET_KEY"] = "access"
    app.config["REFRESH_SECRET_KEY"] = "refresh"
    db.init_app(app)
    with app.app_context():
        architect = Architect(app=app)

        @app.errorhandler(CustomHTTPException)
        def handle_custom(exc: CustomHTTPException):
            return create_response(
                status=exc.status_code,
                errors={"error": exc.error, "reason": exc.reason},
            )

        @app.route("/jwt")
        @architect.schema_constructor(model=User, output_schema=UsernameSchema)
        def jwt_route() -> dict[str, str]:
            """Return the authenticated user's name for verification."""
            return {"username": current_user.username}

        db.create_all()
        RefreshToken.metadata.create_all(bind=db.engine)
        user = User(
            username="carol",
            password_hash=generate_password_hash("pass"),
            api_key_hash=generate_password_hash("key"),
        )
        db.session.add(user)
        db.session.commit()
        access = generate_access_token(user)
        refresh = generate_refresh_token(user)
        yield app.test_client(), access, refresh


def _create_app_with_docs() -> Flask:
    """Create an app configured for JWT auth with documentation."""
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_ENGINE_OPTIONS={"poolclass": StaticPool},
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        FULL_AUTO=False,
        API_CREATE_DOCS=True,
        API_AUTHENTICATE_METHOD=["jwt"],
        API_USER_MODEL=User,
        API_USER_LOOKUP_FIELD="username",
        API_BASE_MODEL=User,
        API_DESCRIPTION="desc",
    )
    app.config["ACCESS_SECRET_KEY"] = "access"
    app.config["REFRESH_SECRET_KEY"] = "refresh"
    db.init_app(app)
    return app


def test_auth_routes_in_spec() -> None:
    """Authentication routes should be tagged and documented."""
    app = _create_app_with_docs()
    with app.app_context():
        architect = Architect(app=app)
        architect.init_api(app=app, api_full_auto=False)
        architect.api.make_auth_routes()
        register_routes_with_spec(architect, architect.route_spec)
        client = app.test_client()
        spec = client.get("/docs/apispec.json").get_json()

    assert spec["paths"]["/auth/login"]["post"]["tags"] == ["Authentication"]
    assert spec["paths"]["/auth/login"]["post"]["summary"] == "Authenticate user and return JWT tokens."
    assert spec["paths"]["/auth/logout"]["post"]["tags"] == ["Authentication"]
    assert spec["paths"]["/auth/logout"]["post"]["summary"] == "Log out current user."
    assert spec["paths"]["/auth/refresh"]["post"]["tags"] == ["Authentication"]
    assert spec["paths"]["/auth/refresh"]["post"]["summary"] == "Refresh access token."


@pytest.fixture()
def client_custom() -> Generator[FlaskClient, None, None]:
    """Create a test client using a custom authentication callback."""

    def custom_auth() -> bool:
        """Simple custom authentication using a fixed token."""
        if request.headers.get("Authorization") != "Custom secret":
            return False
        user = User.query.first()
        if user:
            set_current_user(user)
            return True
        return False

    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        FULL_AUTO=False,
        API_CREATE_DOCS=False,
        API_AUTHENTICATE_METHOD=["custom"],
        API_CUSTOM_AUTH=custom_auth,
    )
    db.init_app(app)
    with app.app_context():
        architect = Architect(app=app)

        @app.errorhandler(CustomHTTPException)
        def handle_custom(exc: CustomHTTPException):
            return create_response(
                status=exc.status_code,
                errors={"error": exc.error, "reason": exc.reason},
            )

        @app.route("/custom")
        @architect.schema_constructor(model=User, output_schema=UsernameSchema)
        def custom_route() -> dict[str, str]:
            """Return the authenticated user's name for verification."""
            return {"username": current_user.username}

        db.create_all()
        user = User(
            username="diana",
            password_hash=generate_password_hash("pass"),
            api_key_hash=generate_password_hash("key"),
        )
        db.session.add(user)
        db.session.commit()
        yield app.test_client()


def assert_unauthorized(resp: Response) -> None:
    """Assert unauthorized response and cleared user context.

        Args:<<<<<<< arched/add-test-cases-for-authentication-errors
    329


            resp (Response): Flask response object to verify.
    """
    assert resp.status_code == 401
    assert get_current_user() is None


def test_basic_success_and_failure(client_basic: FlaskClient) -> None:
    """Test basic authentication and ensure user context resets."""
    assert get_current_user() is None

    credentials = base64.b64encode(b"alice:wonderland").decode("utf-8")
    resp = client_basic.get("/basic", headers={"Authorization": f"Basic {credentials}"})
    assert resp.status_code == 200
    assert resp.get_json()["value"]["username"] == "alice"
    assert get_current_user() is None

    bad_credentials = base64.b64encode(b"alice:wrong").decode("utf-8")
    resp_bad = client_basic.get("/basic", headers={"Authorization": f"Basic {bad_credentials}"})
    assert resp_bad.status_code == 401
    assert get_current_user() is None


def test_basic_login(client_basic: FlaskClient) -> None:
    """Validate basic login endpoint with correct and incorrect credentials."""

    credentials = base64.b64encode(b"alice:wonderland").decode("utf-8")
    resp = client_basic.post("/auth/login", headers={"Authorization": f"Basic {credentials}"})
    assert resp.status_code == 200
    assert resp.get_json()["value"]["username"] == "alice"

    bad_credentials = base64.b64encode(b"alice:bad").decode("utf-8")
    resp_bad = client_basic.post("/auth/login", headers={"Authorization": f"Basic {bad_credentials}"})
    assert resp_bad.status_code == 401


def test_api_key_success_and_failure(client_api_key: FlaskClient) -> None:
    """Test API key authentication and ensure user context resets."""
    assert get_current_user() is None

    resp = client_api_key.get("/key", headers={"Authorization": "Api-Key secret"})
    assert resp.status_code == 200
    assert resp.get_json()["value"]["username"] == "bob"
    assert get_current_user() is None

    resp_bad = client_api_key.get("/key", headers={"Authorization": "Api-Key invalid"})
    assert resp_bad.status_code == 401
    assert get_current_user() is None


def test_api_key_login(client_api_key: FlaskClient) -> None:
    """Validate API key login endpoint."""

    resp = client_api_key.post("/auth/login", headers={"Authorization": "Api-Key secret"})
    assert resp.status_code == 200
    assert resp.get_json()["value"]["username"] == "bob"

    resp_bad = client_api_key.post("/auth/login", headers={"Authorization": "Api-Key wrong"})
    assert resp_bad.status_code == 401


def test_jwt_success_and_failure(client_jwt: tuple[FlaskClient, str, str]) -> None:
    """Test JWT authentication, refresh, and ensure user context resets."""
    client, access_token, refresh_token = client_jwt
    assert get_current_user() is None

    resp = client.get("/jwt", headers={"Authorization": f"Bearer {access_token}"})
    assert resp.status_code == 200
    assert resp.get_json()["value"]["username"] == "carol"
    assert get_current_user() is None

    with client.application.app_context():
        new_access_token, user = refresh_access_token(refresh_token)
        assert user.username == "carol"
        assert get_refresh_token(refresh_token) is None
    resp_new = client.get("/jwt", headers={"Authorization": f"Bearer {new_access_token}"})
    assert resp_new.status_code == 200
    assert resp_new.get_json()["value"]["username"] == "carol"
    assert get_current_user() is None

    resp_bad = client.get("/jwt", headers={"Authorization": "Bearer bad"})
    assert resp_bad.status_code == 401
    assert get_current_user() is None

    with client.application.app_context(), pytest.raises(CustomHTTPException):
        refresh_access_token(refresh_token)
    assert get_current_user() is None


def test_refresh_access_token_missing_key(monkeypatch, client_jwt: tuple[FlaskClient, str, str]) -> None:
    """``refresh_access_token`` raises when ``REFRESH_SECRET_KEY`` is absent."""

    client, _, refresh_token = client_jwt
    monkeypatch.delenv("REFRESH_SECRET_KEY", raising=False)
    client.application.config.pop("REFRESH_SECRET_KEY", None)

    with (
        client.application.app_context(),
        pytest.raises(CustomHTTPException) as exc_info,
    ):
        refresh_access_token(refresh_token)

    assert exc_info.value.status_code == 500
    assert exc_info.value.reason == "REFRESH_SECRET_KEY missing"


def test_jwt_expiry_config(client_jwt: tuple[FlaskClient, str, str]) -> None:
    """Tokens honour ``API_JWT_EXPIRY_TIME`` settings."""

    client, _, _ = client_jwt
    app: Flask = client.application
    with app.app_context():
        app.config["API_JWT_EXPIRY_TIME"] = 1
        app.config["API_JWT_REFRESH_EXPIRY_TIME"] = 2
        user = User.query.filter_by(username="carol").first()
        access = generate_access_token(user)
        refresh = generate_refresh_token(user)
        access_payload = decode_token(access, app.config["ACCESS_SECRET_KEY"])
        refresh_payload = decode_token(refresh, app.config["REFRESH_SECRET_KEY"])
        access_delta = datetime.datetime.fromtimestamp(access_payload["exp"], datetime.timezone.utc) - datetime.datetime.fromtimestamp(access_payload["iat"], datetime.timezone.utc)
        refresh_delta = datetime.datetime.fromtimestamp(refresh_payload["exp"], datetime.timezone.utc) - datetime.datetime.fromtimestamp(refresh_payload["iat"], datetime.timezone.utc)
        assert access_delta == datetime.timedelta(minutes=1)
        assert refresh_delta == datetime.timedelta(minutes=2)


def test_jwt_algorithm_config(client_jwt: tuple[FlaskClient, str, str]) -> None:
    """Tokens honour the algorithm set in configuration."""

    client, _, _ = client_jwt
    app: Flask = client.application
    with app.app_context():
        app.config["API_JWT_ALGORITHM"] = "HS512"
        user = User.query.filter_by(username="carol").first()
        access = generate_access_token(user)
        header = jwt.get_unverified_header(access)
        assert header["alg"] == "HS512"
        payload = decode_token(access, app.config["ACCESS_SECRET_KEY"])
        assert payload["username"] == "carol"


def test_jwt_no_authorization_header(
    client_jwt: tuple[FlaskClient, str, str],
) -> None:
    """Ensure JWT auth fails without an Authorization header."""
    client, _, _ = client_jwt
    assert get_current_user() is None
    resp = client.get("/jwt")
    assert_unauthorized(resp)


def test_jwt_missing_bearer_prefix(
    client_jwt: tuple[FlaskClient, str, str],
) -> None:
    """Reject tokens lacking the Bearer prefix."""
    client, access_token, _ = client_jwt
    assert get_current_user() is None
    resp = client.get("/jwt", headers={"Authorization": access_token})
    assert_unauthorized(resp)


def test_jwt_expired_token(client_jwt: tuple[FlaskClient, str, str]) -> None:
    """Reject expired JWT access tokens."""
    client, _, _ = client_jwt
    with client.application.app_context():
        user = User.query.filter_by(username="carol").first()
        assert user is not None
        expired_token = generate_access_token(user, expires_in_minutes=-1)
    assert get_current_user() is None
    resp = client.get("/jwt", headers={"Authorization": f"Bearer {expired_token}"})
    assert_unauthorized(resp)


def test_custom_success_and_failure(client_custom: FlaskClient) -> None:
    """Test custom authentication and ensure user context resets."""
    assert get_current_user() is None

    resp = client_custom.get("/custom", headers={"Authorization": "Custom secret"})
    assert resp.status_code == 200
    assert resp.get_json()["value"]["username"] == "diana"
    assert get_current_user() is None

    resp_bad = client_custom.get("/custom", headers={"Authorization": "Wrong token"})
    assert resp_bad.status_code == 401
    assert get_current_user() is None


def test_readme_authentication_section() -> None:
    """Authentication section renders only the active method."""
    config = {
        "API_AUTHENTICATE": True,
        "API_AUTHENTICATE_METHOD": ["jwt"],
        "API_TITLE": "Example",
        "API_JWT_EXPIRY_TIME": 360,
        "API_JWT_REFRESH_EXPIRY_TIME": 2880,
    }
    rendered = generate_readme_html(
        "flarchitect/html/base_readme.MD",
        config=config,
        api_output_example="{}",
        has_rate_limiting=False,
    )
    assert rendered.count("# Authentication") == 1
    assert "## JSON Web Tokens (JWT)" in rendered
    assert "## API Key Authentication" not in rendered
    assert "## Basic Authentication" not in rendered


def test_readme_authentication_absent_when_disabled() -> None:
    """Authentication section is omitted when disabled."""
    config = {"API_AUTHENTICATE": False, "API_TITLE": "Example"}
    rendered = generate_readme_html(
        "flarchitect/html/base_readme.MD",
        config=config,
        api_output_example="{}",
        has_rate_limiting=False,
    )
    assert "# Authentication" not in rendered
