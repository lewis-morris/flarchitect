import importlib.util
from types import SimpleNamespace

from demo.model_extension.model import create_app
from demo.model_extension.model.extensions import db
from demo.model_extension.model.models import Author
from flarchitect.core import simple_cache


def test_fallback_cache_endpoint_expiration_and_query_separation(monkeypatch):
    original_find_spec = importlib.util.find_spec

    def find_spec(name, *args, **kwargs):
        if name == "flask_caching":
            return None
        return original_find_spec(name, *args, **kwargs)

    monkeypatch.setattr(importlib.util, "find_spec", find_spec)
    clock = [1000.0]
    monkeypatch.setattr(simple_cache, "time", SimpleNamespace(time=lambda: clock[0]))
    app = create_app({"API_CACHE_TYPE": "SimpleCache", "API_CACHE_TIMEOUT": 10})
    assert isinstance(app.extensions["flarchitect"].cache, simple_cache.SimpleCache)
    client = app.test_client()

    first = client.get("/api/authors/1")
    assert first.status_code == 200
    original_name = first.get_json()["value"]["first_name"]
    assert original_name != "Fallback updated"

    with app.app_context():
        author = db.session.get(Author, 1)
        author.first_name = "Fallback updated"
        db.session.commit()

    clock[0] = 1005.0
    cached = client.get("/api/authors/1")
    assert cached.status_code == 200
    assert cached.get_json()["value"] == first.get_json()["value"]

    # A different query string has its own entry and sees the updated record.
    selected = client.get("/api/authors/1?fields=id,first_name")
    assert selected.status_code == 200
    assert selected.get_json()["value"]["first_name"] == "Fallback updated"
    assert client.get("/api/authors/1").get_json()["value"] == first.get_json()["value"]

    # The existing backend treats the exact expiry timestamp as still valid.
    clock[0] = 1010.0
    assert client.get("/api/authors/1").get_json()["value"] == first.get_json()["value"]
    clock[0] = 1010.001
    refreshed = client.get("/api/authors/1")
    assert refreshed.status_code == 200
    assert refreshed.get_json()["value"]["first_name"] == "Fallback updated"
