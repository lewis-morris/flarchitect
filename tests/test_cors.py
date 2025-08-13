"""Tests for Cross-Origin Resource Sharing (CORS) support."""

from demo.model_extension.model import create_app


def test_cors_headers():
    """Ensure CORS headers are included when enabled."""
    app = create_app(
        {
            "API_ENABLE_CORS": True,
            "CORS_RESOURCES": {r"/api/*": {"origins": "http://example.com"}},
        }
    )
    client = app.test_client()
    response = client.get("/api/authors", headers={"Origin": "http://example.com"})
    assert response.headers["Access-Control-Allow-Origin"] == "http://example.com"
