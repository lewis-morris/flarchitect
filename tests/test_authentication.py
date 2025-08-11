import base64

import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema
from werkzeug.security import check_password_hash, generate_password_hash

from flarchitect.core.architect import Architect
from flarchitect.exceptions import CustomHTTPException
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

    @staticmethod
    def get_session():
        return db.session


@pytest.fixture()
def client_basic():
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

        @app.errorhandler(CustomHTTPException)
        def handle_custom(exc: CustomHTTPException):
            return create_response(
                status=exc.status_code,
                errors={"error": exc.error, "reason": exc.reason},
            )

        class DummySchema(Schema):
            pass

        @app.route("/basic")
        @architect.schema_constructor(model=User, output_schema=DummySchema)
        def basic_route():
            return {"value": True}

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
def client_api_key():
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

        class DummySchema(Schema):
            pass

        @app.route("/key")
        @architect.schema_constructor(model=User, output_schema=DummySchema)
        def key_route():
            return {"value": True}

        db.create_all()
        user = User(
            username="bob",
            password_hash=generate_password_hash("pw"),
            api_key_hash=generate_password_hash("secret"),
        )
        db.session.add(user)
        db.session.commit()
        yield app.test_client()


def test_basic_success_and_failure(client_basic):
    credentials = base64.b64encode(b"alice:wonderland").decode("utf-8")
    resp = client_basic.get("/basic", headers={"Authorization": f"Basic {credentials}"})
    assert resp.status_code == 200

    bad_credentials = base64.b64encode(b"alice:wrong").decode("utf-8")
    resp_bad = client_basic.get(
        "/basic", headers={"Authorization": f"Basic {bad_credentials}"}
    )
    assert resp_bad.status_code == 401


def test_api_key_success_and_failure(client_api_key):
    resp = client_api_key.get("/key", headers={"Authorization": "Api-Key secret"})
    assert resp.status_code == 200

    resp_bad = client_api_key.get(
        "/key", headers={"Authorization": "Api-Key invalid"}
    )
    assert resp_bad.status_code == 401
