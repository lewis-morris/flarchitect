import time

from demo.model_extension.model import create_app
from demo.model_extension.model.extensions import db
from demo.model_extension.model.models import Author


def test_get_endpoint_cached_response():
    app = create_app({"API_CACHE_TYPE": "SimpleCache", "API_CACHE_TIMEOUT": 1})
    client = app.test_client()

    first = client.get("/api/authors/1").get_json()["value"]["first_name"]

    with app.app_context():
        author = db.session.get(Author, 1)
        author.first_name = "Cached"
        db.session.commit()

    second = client.get("/api/authors/1").get_json()["value"]["first_name"]
    assert second == first

    time.sleep(1.1)

    third = client.get("/api/authors/1").get_json()["value"]["first_name"]
    assert third == "Cached"
