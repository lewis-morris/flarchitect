import pytest

from demo.basic_factory.basic_factory import create_app


@pytest.fixture
def new_app():
    new_app = create_app(
        {
            "API_TITLE": "Automated test",
            "API_VERSION": "0.2.0",
            "API_ADD_RELATIONS": True,
            # Other configurations specific to this test
        }
    )
    with new_app.app_context():
        yield new_app


@pytest.fixture
def new_client(new_app):
    return new_app.test_client()


@pytest.fixture
def app_two():
    app_two = create_app(
        {
            "API_TITLE": "Automated test",
            "API_VERSION": "0.2.0",
            # Other configurations specific to this test
        }
    )
    with app_two.app_context():
        yield app_two


@pytest.fixture
def client_two(app_two):
    return app_two.test_client()


def test_get(new_client):
    get_resp = new_client.get("/api/books/1")
    get_resp_none = new_client.get("/api/books/99999")
    get_resp_child = new_client.get("/api/authors/1/books")

    assert get_resp.status_code == 200
    assert get_resp.json["value"]["id"] == 1

    assert get_resp_none.status_code == 404

    assert get_resp_child.status_code == 200
    assert len(get_resp_child.json["value"]) > 0

    assert get_resp_child.json["value"][0]["author_id"] == 1


def test_delete(client_two):
    delete_response = client_two.delete("/api/reviews/1")
    get_response = client_two.get("/api/reviews/1")
    delete_response_fail = client_two.delete("/api/reviews/1")

    assert delete_response.status_code == 200
    assert get_response.json["value"] is None
    assert get_response.status_code == 404

    assert delete_response_fail.status_code == 404
    assert delete_response_fail.json["errors"]["error"] == ("Review not found.")

    books_pre_delete = client_two.get("/api/authors/2/books")
    resp_delete_fail = client_two.delete("/api/authors/2")
    resp_delete_related = client_two.delete("/api/authors/2?cascade_delete=1")

    assert books_pre_delete.status_code == 200
    assert len(books_pre_delete.json["value"]) > 0
    assert resp_delete_fail.status_code == 409
    assert resp_delete_related.status_code == 200

    books_post_delete = client_two.get("/api/authors/2/books")
    assert books_post_delete.status_code == 404

    book_id = books_pre_delete.json["value"][0]["id"]
    books_post_delete = client_two.get(f"/api/books/{book_id}")
    assert books_post_delete.status_code == 404


def test_patch(new_client):
    get_response = new_client.get("/api/books/3")
    data = get_response.json
    data["value"]["title"] = "New Title"
    patch_response = new_client.patch("/api/books/3", json=data["value"])
    new_get_response = new_client.get("/api/books/3")

    assert patch_response.status_code == 200
    assert new_get_response.json["value"]["title"] == "New Title"


def test_hybrid_and_patch(new_client):
    get_response = new_client.get("/api/authors/1")
    data = get_response.json
    data["value"]["first_name"] = "Foo"
    data["value"]["last_name"] = "Bar"
    patch_response = new_client.patch("/api/authors/1", json=data["value"])
    new_get_response = new_client.get("/api/authors/1")

    assert patch_response.status_code == 200
    assert new_get_response.json["value"]["full_name"] == "Foo Bar"


def test_post(new_client):
    data = {
        "biography": "Foo is a Baz",
        "date_of_birth": "1900-01-01",
        "first_name": "Foo",
        "last_name": "Bar",
        "nationality": "Bazville",
        "website": "https://foobar.baz",
    }

    post_response = new_client.post("/api/authors", json=data)
    new_id = post_response.json["value"]["id"]

    get_response = new_client.get(f"/api/authors/{new_id}")

    assert post_response.status_code == 200
    assert post_response.json["value"]["full_name"] == "Foo Bar"

    assert get_response.status_code == 200
    assert get_response.json["value"]["full_name"] == "Foo Bar"


def test_basic_get_books(new_client):
    response = new_client.get("/api/books")
    assert isinstance(response.json["value"], list)
    assert "isbn" in response.json["value"][0]
    assert "title" in response.json["value"][0]


def test_patch_deleted(new_client):
    review_pre_delete = new_client.get("/api/reviews/1")
    resp_delete = new_client.delete("/api/reviews/1")

    review_data = review_pre_delete.json["value"]
    review_data["title"] = "New Title"

    resp_patch_fail = new_client.patch("/api/reviews/1", json=review_data)

    assert resp_delete.status_code == 200
    assert resp_patch_fail.status_code == 404
