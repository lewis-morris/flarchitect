import pytest
from flask import Flask

from flarchitect.core.architect import Architect


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    if config:
        app.config.update(config)
    with app.app_context():
        Architect(app)

    @app.get("/ping")
    def ping() -> str:
        return "pong"

    return app


@pytest.fixture
def client_with_cors() -> Flask.test_client:  # type: ignore[name-defined]
    app = create_app(
        {
            "API_ENABLE_CORS": True,
            "CORS_RESOURCES": {r"/ping": {"origins": "*"}},
            "FULL_AUTO": False,
            "API_CREATE_DOCS": False,
        }
    )
    return app.test_client()


@pytest.fixture
def client_without_cors() -> Flask.test_client:  # type: ignore[name-defined]
    app = create_app(
        {
            "API_ENABLE_CORS": False,
            "FULL_AUTO": False,
            "API_CREATE_DOCS": False,
        }
    )
    return app.test_client()


def test_cors_header_present(client_with_cors) -> None:
    response = client_with_cors.get("/ping", headers={"Origin": "http://example.com"})
    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") is not None


def test_cors_header_absent(client_without_cors) -> None:
    response = client_without_cors.get("/ping", headers={"Origin": "http://example.com"})
    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" not in response.headers
