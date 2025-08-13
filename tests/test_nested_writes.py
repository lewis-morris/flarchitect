import pytest

from demo.basic_factory.basic_factory import create_app


@pytest.fixture
def client():
    app = create_app(
        {
            "API_TITLE": "Automated test",
            "API_VERSION": "0.2.0",
            "API_ALLOW_NESTED_WRITES": True,
        }
    )
    with app.app_context():
        yield app.test_client()


def test_post_author_with_two_books(client):
    data = {
        "first_name": "Nested",
        "last_name": "Author",
        "biography": "Bio",
        "date_of_birth": "1990-01-01",
        "nationality": "US",
        "books": [
            {
                "title": "Book 1",
                "isbn": "11111",
                "publication_date": "2024-01-01",
                "publisher_id": 1,
                "author_id": 0,
            },
            {
                "title": "Book 2",
                "isbn": "22222",
                "publication_date": "2024-01-02",
                "publisher_id": 1,
                "author_id": 0,
            },
        ],
    }
    resp = client.post("/api/authors", json=data)
    assert resp.status_code == 200
    author_id = resp.json["value"]["id"]
    books_resp = client.get(f"/api/authors/{author_id}/books")
    assert books_resp.status_code == 200
    assert len(books_resp.json["value"]) == 2


def test_post_publisher_with_two_authors(client):
    data = {
        "name": "Pub Nested",
        "website": "https://pubnested.com",
        "foundation_year": 2020,
        "books": [
            {
                "title": "PB1",
                "isbn": "33333",
                "publication_date": "2024-01-01",
                "author_id": 0,
                "publisher_id": 0,
                "author": {
                    "first_name": "A1",
                    "last_name": "B1",
                    "biography": "Bio",
                    "date_of_birth": "1980-01-01",
                    "nationality": "US",
                },
            },
            {
                "title": "PB2",
                "isbn": "44444",
                "publication_date": "2024-01-02",
                "author_id": 0,
                "publisher_id": 0,
                "author": {
                    "first_name": "A2",
                    "last_name": "B2",
                    "biography": "Bio",
                    "date_of_birth": "1981-01-01",
                    "nationality": "US",
                },
            },
        ],
    }
    resp = client.post("/api/publishers", json=data)
    assert resp.status_code == 200
    pub_id = resp.json["value"]["id"]
    books_resp = client.get(f"/api/publishers/{pub_id}/books")
    assert books_resp.status_code == 200
    assert len(books_resp.json["value"]) == 2
    author_ids = {book["author_id"] for book in books_resp.json["value"]}
    assert len(author_ids) == 2


def test_post_book_with_author_and_publisher(client):
    data = {
        "title": "Standalone",
        "isbn": "99999",
        "publication_date": "2024-01-01",
        "author_id": 0,
        "publisher_id": 0,
        "author": {
            "first_name": "Nested",
            "last_name": "Writer",
            "biography": "Bio",
            "date_of_birth": "1980-01-01",
            "nationality": "US",
        },
        "publisher": {
            "name": "Nested Pub",
            "website": "https://nestedpub.com",
            "foundation_year": 2021,
        },
    }
    resp = client.post("/api/books", json=data)
    assert resp.status_code == 200


def test_nested_write_missing_required_field(client):
    """A nested write missing required fields should return an error response."""

    data = {
        "first_name": "Bad",
        "last_name": "Author",
        "biography": "Bio",
        "date_of_birth": "1990-01-01",
        "nationality": "US",
        "books": [
            {
                # missing title field
                "isbn": "55555",
                "publication_date": "2024-01-01",
                "publisher_id": 1,
                "author_id": 0,
            }
        ],
    }
    resp = client.post("/api/authors", json=data)
    body = resp.get_json()
    assert resp.status_code == 400
    assert body["errors"]["error"]["books"]["0"]["title"][0] == "Missing data for required field."
