import pytest

from demo.basic_factory.basic_factory import create_app


@pytest.fixture
def app():
    app = create_app({"API_ALLOW_JOIN": True})
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_join_respects_limit_and_total_count_on_base(client):
    # Baseline without join
    base = client.get("/api/authors?limit=2").get_json()
    assert base["status_code"] == 200
    base_total = base["total_count"]
    assert isinstance(base_total, int) and base_total >= 2

    # Join a one-to-many relationship that can multiply rows
    joined = client.get("/api/authors?join=books&limit=1").get_json()
    assert joined["status_code"] == 200

    # Limit should apply to distinct base rows
    assert len(joined["value"]) == 1

    # total_count should reflect distinct base entities, not multiplied rows
    assert joined["total_count"] == base_total

