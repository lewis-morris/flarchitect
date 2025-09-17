from demo.basic_factory.basic_factory import create_app


def test_docs_spec_default_route() -> None:
    """Default docs spec route serves JSON under /docs."""
    app = create_app()
    client = app.test_client()
    # HTML references the docs-scoped spec JSON
    html = client.get("/docs").get_data(as_text=True)
    assert 'apispec.json' in html
    # JSON is served at the default path
    resp = client.get("/docs/apispec.json")
    assert resp.status_code == 200
    assert resp.is_json
    assert resp.get_json().get("openapi")


def test_docs_spec_custom_route() -> None:
    """Docs spec route is configurable via API_DOCS_SPEC_ROUTE."""
    app = create_app({"API_DOCS_SPEC_ROUTE": "/docs/spec.json"})
    client = app.test_client()
    html = client.get("/docs").get_data(as_text=True)
    assert 'spec.json' in html
    resp = client.get("/docs/spec.json")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, dict)
    assert data.get("openapi")

