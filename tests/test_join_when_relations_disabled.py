import pytest

try:  # pragma: no cover - optional imports for minimal envs
    from demo.basic_factory.basic_factory import create_app
except ModuleNotFoundError:  # pragma: no cover
    create_app = None


pytestmark = pytest.mark.skipif(create_app is None, reason="demo app not available")


@pytest.fixture
def app_rel_disabled():
    app = create_app(
        {
            "API_ALLOW_JOIN": True,
            "API_ADD_RELATIONS": False,
            "API_SERIALIZATION_TYPE": "dynamic",
        }
    )
    yield app


@pytest.fixture
def client_rel_disabled(app_rel_disabled):
    return app_rel_disabled.test_client()


def test_dynamic_join_includes_relation_when_relations_disabled(client_rel_disabled):
    # Without join token, relationships should not appear in payload
    no_join = client_rel_disabled.get("/api/books/1").json
    assert "author" not in no_join["value"]

    # With join token, the requested relationship should be present as nested object
    with_join = client_rel_disabled.get("/api/books/1?join=authors").json
    assert isinstance(with_join["value"].get("author"), dict)
    assert with_join["status_code"] == 200


def test_joined_select_fields_fall_back_to_dictionary(client_rel_disabled):
    # Select a base field and a joined-table field; ensure keys are preserved
    resp = client_rel_disabled.get("/api/books?join=authors&fields=title,author.first_name").json
    assert resp["status_code"] == 200
    assert isinstance(resp["value"], list)
    assert len(resp["value"]) > 0
    row = resp["value"][0]
    # The dictionary fallback should preserve raw keys from the result row
    assert "title" in row
    assert "first_name" in row
