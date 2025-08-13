import pytest

from demo.basic_factory.basic_factory import create_app
from demo.model_extension.model import create_app as create_app_models


@pytest.fixture
def app():
    app = create_app(
        {
            "API_TITLE": "Automated test",
            "API_VERSION": "0.2.0",
            # Other configurations specific to this test
        }
    )
    yield app
    del app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def app_models():
    app_models = create_app_models(
        {
            "API_TITLE": "Automated test",
            "API_VERSION": "0.2.0",
            # Other configurations specific to this test
        }
    )
    yield app_models
    del app_models


@pytest.fixture
def client_models(app_models):
    return app_models.test_client()


def test_patch_not_full_field(client):
    # Assuming 'first_name' and 'last_name' combination must be unique
    # Provide data that duplicates an existing author's name
    duplicate_data = {
        "first_name": None,
        "last_name": None,
    }
    response = client.patch("/api/authors/1", json=duplicate_data)
    assert response.status_code == 422
    assert "NOT NULL constraint failed" in response.json["errors"]["error"]


def test_invalid_type(client):
    author = client.get("/api/authors/1").json
    assert author["status_code"] == 200

    data = author["value"]
    data["date_of_birth"] = 3
    patch_resp = client.patch("/api/authors/1", json=data)
    assert patch_resp.status_code == 400

    assert patch_resp.json["errors"]["error"]["date_of_birth"][0] == "Not a valid date."


def test_invalid_type_datatype(client):
    review = client.get("/api/reviews/1").json

    data = review["value"]
    data["rating"] = "s"
    patch_resp = client.patch("/api/reviews/1", json=data)
    assert patch_resp.status_code == 400

    assert patch_resp.json["errors"]["error"]["rating"][0] == "Not a valid number."


def test_invalid_type_datatype_two(client_models):
    author = client_models.get("/api/publishers/1").json
    data = author["value"]
    data["email"] = "foo"
    patch_resp = client_models.patch("/api/publishers/1", json=data)

    assert patch_resp.status_code == 400
    assert patch_resp.json["errors"]["error"]["email"][0] == "Email address is not valid."


def test_invalid_url(client_models):
    """Invalid URLs return a clear validation error."""
    publisher = client_models.get("/api/publishers/1").json
    data = publisher["value"]
    data["website"] = "not-a-url"
    resp = client_models.patch("/api/publishers/1", json=data)

    assert resp.status_code == 400
    assert resp.json["errors"]["error"]["website"][0] == "URL is not valid."
