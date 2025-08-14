from demo.advanced_features.app import create_app


def _create_client():
    """Helper to create app and test client."""
    app = create_app()
    return app, app.test_client()


def test_title_capitalised_and_nested_author():
    """Book titles should be capitalised via the add callback and nested author created."""
    app, client = _create_client()
    res = client.post(
        "/api/books",
        json={"title": "my book", "author": {"name": "alice", "email": "alice@example.com"}},
    )
    data = res.get_json()
    assert res.status_code == 200
    assert data["value"]["title"] == "My Book"
    assert data["value"]["author"].endswith("/1")


def test_email_validation():
    """Invalid author email should trigger a validation error."""
    app, client = _create_client()
    res = client.post(
        "/api/books",
        json={"title": "another", "author": {"name": "bob", "email": "not-an-email"}},
    )
    data = res.get_json()
    assert res.status_code == 400
    assert "email" in data["errors"]["error"]["author"]


def test_disallowed_method():
    """Author PATCH endpoint is disallowed via Meta.allowed_methods."""
    app, client = _create_client()
    post = client.post(
        "/api/books",
        json={"title": "nested", "author": {"name": "carol", "email": "carol@example.com"}},
    ).get_json()
    author_url = post["value"]["author"]
    author_id = author_url.rsplit("/", 1)[-1]
    res = client.patch(f"/api/author/{author_id}", json={"name": "changed"})
    assert res.status_code == 404
