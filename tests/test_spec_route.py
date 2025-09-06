from demo.basic_factory.basic_factory import create_app


def test_default_spec_route():
    """The OpenAPI spec JSON is served under docs by default."""
    app = create_app()
    client = app.test_client()
    resp = client.get("/docs/apispec.json")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, dict)
    assert data.get("openapi")
    assert data["components"]["securitySchemes"]["bearerAuth"] == {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }


def test_custom_spec_route():
    """Docs spec route can be overridden via configuration."""
    app = create_app({"API_DOCS_SPEC_ROUTE": "/docs/spec.json"})
    client = app.test_client()
    resp = client.get("/docs/spec.json")
    assert resp.status_code == 200
    assert resp.get_json().get("openapi")


def test_openapi_route_redirects_to_docs():
    """Top-level /openapi.json redirects to the docs JSON for compatibility."""
    app = create_app()
    client = app.test_client()
    resp = client.get("/openapi.json", follow_redirects=False)
    assert resp.status_code in (301, 302, 307, 308)
