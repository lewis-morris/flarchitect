import time

from demo.caching.app import Author, create_app, db


def test_cached_endpoint_stores_and_invalidates_response():
    app = create_app({"API_CACHE_TIMEOUT": 1})
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
