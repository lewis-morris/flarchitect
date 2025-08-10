import pytest

from demo.model_extension.model import create_app


@pytest.fixture
def app_model_meta():
    app_model_meta = create_app(
        {
            "API_TITLE": "Automated test",
            "API_VERSION": "0.2.0",
            # Other configurations specific to this test
        }
    )
    yield app_model_meta


@pytest.fixture
def client_meta_model(app_model_meta):
    return app_model_meta.test_client()


def test_model_block_methods(client_meta_model):

    fail_get = client_meta_model.get("/api/categories/1")
    assert fail_get.status_code == 405
