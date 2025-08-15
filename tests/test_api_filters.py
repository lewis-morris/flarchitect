import pytest

from demo.basic_factory.basic_factory import create_app


@pytest.fixture
def app():
    app = create_app(
        {
            "API_TITLE": "Automated test",
            "API_VERSION": "0.2.0",
        }
    )
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_basic_select(client):
    response = client.get("/api/books?fields=isbn,title")
    assert isinstance(response.json["value"], list)
    assert "isbn" in response.json["value"][0]
    assert "title" in response.json["value"][0]
    assert "publication_date" not in response.json["value"][0]


def test_basic_filter(client):
    book_id = client.get("/api/books/1").json["value"]["id"]
    filtered_books = client.get("/api/books?id__eq=1").json["value"]

    assert filtered_books[0]["id"] == book_id
    assert len(filtered_books) == 1


def test_advanced_filter(client):
    author = client.get("/api/authors/2").json["value"]

    eq = client.get("/api/authors?first_name__eq=" + author["first_name"]).json["value"]
    assert eq[0]["first_name"] == author["first_name"]

    ne = client.get("/api/authors?first_name__ne=" + author["first_name"]).json["value"]
    assert ne[0]["first_name"] != author["first_name"]

    lt = client.get(f"/api/authors?id__lt={author['id']}").json["value"]
    assert lt[0]["id"] == 1

    le = client.get(f"/api/authors?id__le={author['id']}").json["value"]
    assert le[0]["id"] == 1 or le[0]["id"] == 2

    gt = client.get(f"/api/authors?id__gt={author['id']}").json["value"]
    assert gt[0]["id"] != 1 and gt[0]["id"] != 2

    ge = client.get(f"/api/authors?id__ge={author['id']}").json["value"]
    assert ge[0]["id"] != 1

    _in = client.get("/api/authors?id__in=(10,11,12)").json["value"]
    assert _in[0]["id"] in [10, 11, 12]

    nin = client.get("/api/authors?id__nin=(1,2,3)").json["value"]
    assert nin[0]["id"] not in [1, 2, 3]

    like = client.get("/api/authors?full_name__like=" + author["first_name"]).json["value"]
    assert author["full_name"] in [a["full_name"] for a in like]

    ilike = client.get("/api/authors?full_name__ilike=" + author["first_name"].lower()).json["value"]
    assert author["full_name"] in [a["full_name"] for a in ilike]

    author_ONE = client.get("/api/authors/2").json["value"]["id"]
    author_TWO = client.get("/api/authors/3").json["value"]["id"]

    eq_or = client.get(f"/api/authors?or[id__eq={author_ONE}, id__eq={author_TWO}]").json["value"]
    ids = [author["id"] for author in eq_or]
    assert 2 in ids and 3 in ids


def test_basic_pagination(client, app):
    books = client.get("/api/books?order_by=id").json
    assert len(books["value"]) == 20

    books = client.get("/api/books?limit=10&page=1").json
    assert books["next_url"] == "http://localhost/api/books?limit=10&page=2"
    assert books["previous_url"] is None

    books = client.get("/api/books?limit=5&page=2").json
    assert books["next_url"] == "http://localhost/api/books?limit=5&page=3"
    assert books["previous_url"] == "http://localhost/api/books?limit=5&page=1"

    app.config["API_PAGINATION_SIZE_DEFAULT"] = 5
    books = client.get("/api/books?order_by=id").json
    assert len(books["value"]) == 5

    books = client.get("/api/books?order_by=id&limit=10").json
    assert len(books["value"]) == 10

    books = client.get(books["next_url"]).json
    assert len(books["value"]) == 10
    assert books["value"][0]["id"] == 11

    books_error = client.get("/api/books?order_by=id&limit=d")
    assert books_error.status_code == 400

    books_error = client.get("/api/books?order_by=id&page=d&limit=d")
    assert books_error.status_code == 400


def test_basic_sort(client):
    books = client.get("/api/books?order_by=id").json
    assert books["value"][0]["id"] == 1
    books = client.get("/api/books?order_by=-id").json
    assert books["value"][0]["id"] == books["total_count"]
