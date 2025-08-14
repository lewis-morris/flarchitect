import base64

from demo.basic_factory.basic_factory import create_app as factory_app
from demo.scaffolding.module import create_app as scaffold_app


def test_docs_accessible_without_password():
    app = scaffold_app()
    client = app.test_client()
    resp = client.get("/docs")
    assert resp.status_code == 200


def test_docs_password_protected():
    app = factory_app({"API_DOCUMENTATION_PASSWORD": "letmein"})
    client = app.test_client()

    resp = client.get("/docs")
    assert resp.status_code == 401

    token = base64.b64encode(b"user:letmein").decode()
    resp = client.get("/docs", headers={"Authorization": f"Basic {token}"})
    assert resp.status_code == 200
