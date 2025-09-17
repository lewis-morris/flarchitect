"""Tests for JWT hardening: leeway, aud/iss, allowed algs, RS256."""

from __future__ import annotations

import datetime
from collections.abc import Generator

import jwt
import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.pool import StaticPool

from flarchitect.authentication.jwt import decode_token, generate_access_token
from flarchitect.exceptions import CustomHTTPException


db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True)


@pytest.fixture()
def app_ctx() -> Generator[Flask, None, None]:
    app = Flask(__name__)
    with app.app_context():
        yield app


def test_leeway_allows_small_skew(app_ctx: Flask) -> None:
    """Expired tokens within configured leeway decode successfully."""
    app_ctx.config["API_JWT_LEEWAY"] = 30  # seconds
    secret = "access"
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {"sub": "user", "iat": now - datetime.timedelta(seconds=20), "exp": now - datetime.timedelta(seconds=10)}
    token = jwt.encode(payload, secret, algorithm="HS256")
    decoded = decode_token(token, secret)
    assert decoded["sub"] == "user"


def test_issuer_audience_enforced_generation_and_decode(app_ctx: Flask) -> None:
    """Tokens include and enforce iss/aud when configured."""
    # Minimal app and DB to use generator
    app_ctx.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_ENGINE_OPTIONS={"poolclass": StaticPool},
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        API_USER_MODEL=User,
        API_USER_LOOKUP_FIELD="username",
        ACCESS_SECRET_KEY="access",
    )
    app = app_ctx
    db.init_app(app)
    with app.app_context():
        db.create_all()
        user = User(username="alice")
        db.session.add(user)
        db.session.commit()
        app.config["API_JWT_ISSUER"] = "https://issuer.example"
        app.config["API_JWT_AUDIENCE"] = "api-audience"
        token = generate_access_token(user)
        decoded = decode_token(token, app.config["ACCESS_SECRET_KEY"])
        assert decoded["iss"] == "https://issuer.example"
        assert decoded["aud"] == "api-audience"


def test_wrong_audience_rejected(app_ctx: Flask) -> None:
    app_ctx.config["API_JWT_AUDIENCE"] = "right-aud"
    payload = {
        "sub": "user",
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5),
        "aud": "wrong-aud",
    }
    token = jwt.encode(payload, "access", algorithm="HS256")
    with pytest.raises(CustomHTTPException) as exc_info:
        decode_token(token, "access")
    assert exc_info.value.status_code == 401
    assert exc_info.value.reason == "Invalid token"


def test_rs256_generate_and_decode() -> None:
    """Support RS256 with separate private/public keys."""
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
    except Exception:  # pragma: no cover - cryptography not available
        pytest.skip("cryptography not available for RS256 test")

    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_ENGINE_OPTIONS={"poolclass": StaticPool},
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        API_USER_MODEL=User,
        API_USER_LOOKUP_FIELD="username",
        API_JWT_ALGORITHM="RS256",
    )

    # Generate an RSA keypair
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    app.config["ACCESS_PRIVATE_KEY"] = private_pem
    app.config["ACCESS_PUBLIC_KEY"] = public_pem

    db.init_app(app)
    with app.app_context():
        db.create_all()
        user = User(username="bob")
        db.session.add(user)
        db.session.commit()
        token = generate_access_token(user)
        header = jwt.get_unverified_header(token)
        assert header["alg"] == "RS256"
        decoded = decode_token(token, app.config["ACCESS_PUBLIC_KEY"])  # verify with public key
        assert decoded["username"] == "bob"

