from demo.basic_factory.basic_factory import create_app


def test_default_spec_route():
    """The OpenAPI spec is served at the default path."""
    app = create_app()
    client = app.test_client()
    resp = client.get("/openapi.json")
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
    """The spec route can be overridden via configuration."""
    app = create_app({"API_SPEC_ROUTE": "/spec.json"})
    client = app.test_client()
    resp = client.get("/spec.json")
    assert resp.status_code == 200
    assert resp.get_json().get("openapi")
