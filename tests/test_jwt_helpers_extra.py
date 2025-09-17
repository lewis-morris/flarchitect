import os

import pytest
from flask import Flask

from flarchitect.authentication.jwt import (
    _get_access_signing_key,
    _get_access_verifying_key,
    _get_refresh_signing_key,
    _get_refresh_verifying_key,
    get_allowed_algorithms,
    get_jwt_algorithm,
    create_jwt,
)


def test_get_allowed_algorithms_variants(monkeypatch):
    app = Flask(__name__)
    with app.app_context():
        app.config["API_JWT_ALLOWED_ALGORITHMS"] = "HS256,  RS256"
        assert get_allowed_algorithms() == ["HS256", "RS256"]
        app.config["API_JWT_ALLOWED_ALGORITHMS"] = ["HS512", "HS256"]
        assert get_allowed_algorithms() == ["HS512", "HS256"]
        app.config.pop("API_JWT_ALLOWED_ALGORITHMS")
        # falls back to configured algorithm
        app.config["API_JWT_ALGORITHM"] = "HS384"
        assert get_allowed_algorithms() == ["HS384"]


def _clear_env(keys):
    for k in keys:
        os.environ.pop(k, None)


@pytest.mark.parametrize(
    "func, alg, missing_keys, error_msg",
    [
        (_get_access_signing_key, "RS256", ["ACCESS_PRIVATE_KEY", "ACCESS_SECRET_KEY"], "ACCESS_PRIVATE_KEY missing"),
        (_get_access_verifying_key, "RS256", ["ACCESS_PUBLIC_KEY", "ACCESS_SECRET_KEY"], "ACCESS_PUBLIC_KEY missing"),
        (_get_refresh_signing_key, "RS256", ["REFRESH_PRIVATE_KEY", "REFRESH_SECRET_KEY"], "REFRESH_PRIVATE_KEY missing"),
        (_get_refresh_verifying_key, "RS256", ["REFRESH_PUBLIC_KEY", "REFRESH_SECRET_KEY"], "REFRESH_PUBLIC_KEY missing"),
        (_get_access_signing_key, "HS256", ["ACCESS_SECRET_KEY"], "ACCESS_SECRET_KEY missing"),
        (_get_access_verifying_key, "HS256", ["ACCESS_SECRET_KEY"], "ACCESS_SECRET_KEY missing"),
        (_get_refresh_signing_key, "HS256", ["REFRESH_SECRET_KEY"], "REFRESH_SECRET_KEY missing"),
        (_get_refresh_verifying_key, "HS256", ["REFRESH_SECRET_KEY"], "REFRESH_SECRET_KEY missing"),
    ],
)
def test_missing_keys_raise(monkeypatch, func, alg, missing_keys, error_msg):
    app = Flask(__name__)
    with app.app_context():
        _clear_env(missing_keys)
        for k in missing_keys:
            if k in app.config:
                app.config.pop(k)
        with pytest.raises(Exception) as exc:
            func(alg)
        assert error_msg in str(exc.value)


def test_create_jwt_includes_optional_claims():
    app = Flask(__name__)
    with app.app_context():
        app.config["API_JWT_ISSUER"] = "issuer-x"
        app.config["API_JWT_AUDIENCE"] = "aud-x"
        token, payload = create_jwt({"a": 1}, "secret", 1, "HS256")
        assert token
        assert payload["iss"] == "issuer-x"
        assert payload["aud"] == "aud-x"

