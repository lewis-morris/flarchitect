from demo.basic_factory.basic_factory import create_app


def test_swagger_docs_served():
    app = create_app({"API_DOCS_STYLE": "swagger"})
    client = app.test_client()
    resp = client.get("/docs")
    assert resp.status_code == 200
    assert "SwaggerUIBundle" in resp.get_data(as_text=True)
