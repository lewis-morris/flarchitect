"""Tests ensuring spec URLs honor documentation prefix."""

from demo.basic_factory.basic_factory import create_app


def test_redoc_spec_url_respects_prefix() -> None:
    """Redoc template should reference prefixed swagger spec."""
    app = create_app({"DOCUMENTATION_URL_PREFIX": "/api"})
    client = app.test_client()
    resp = client.get("/api/docs")
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert 'spec-url="/api/docs/apispec.json"' in html


def test_swagger_spec_url_respects_prefix() -> None:
    """Swagger template should reference prefixed swagger spec."""
    app = create_app({"DOCUMENTATION_URL_PREFIX": "/api", "API_DOCS_STYLE": "swagger"})
    client = app.test_client()
    resp = client.get("/api/docs")
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert 'url: "/api/docs/apispec.json"' in html
