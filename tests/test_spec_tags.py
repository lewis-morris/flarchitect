"""Tests for tag registration in OpenAPI specs."""

from demo.basic_factory.basic_factory import create_app


def test_spec_contains_tags() -> None:
    """Ensure that generated specs include root-level tag definitions."""
    app = create_app()
    client = app.test_client()
    spec = client.get("/docs/apispec.json").get_json()
    assert "tags" in spec
    tag_names = {t["name"] for t in spec["tags"]}
    assert {"Books", "Categories"}.issubset(tag_names)
