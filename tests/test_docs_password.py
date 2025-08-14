from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

from demo.basic_factory.basic_factory import create_app as factory_app
from demo.scaffolding.module import create_app as scaffold_app
from flarchitect import Architect


def test_docs_accessible_without_password():
    app = scaffold_app()
    client = app.test_client()
    resp = client.get("/docs")
    assert resp.status_code == 200


def test_docs_password_protected():
    app = factory_app({"API_DOCUMENTATION_PASSWORD": "letmein"})
    client = app.test_client()

    resp = client.get("/docs")
    assert resp.status_code == 200
    assert b"API Documentation Login" in resp.data

    resp = client.post("/docs", data={"password": "letmein"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"API Documentation Login" not in resp.data


db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True)
    password_hash = db.Column(db.String)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def get_id(self) -> str:
        return str(self.id)

    @property
    def is_active(self) -> bool:
        return True


def auth_app() -> Flask:
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        FULL_AUTO=False,
        API_CREATE_DOCS=True,
        API_AUTHENTICATE_METHOD=["basic"],
        API_USER_MODEL=User,
        API_USER_LOOKUP_FIELD="username",
        API_CREDENTIAL_CHECK_METHOD="check_password",
        API_DOCUMENTATION_REQUIRE_AUTH=True,
        API_BASE_MODEL=db.Model,
        SECRET_KEY="test",
    )
    db.init_app(app)
    with app.app_context():
        architect = Architect(app=app)
        architect.init_api(app=app, api_full_auto=False)
        architect.api.make_auth_routes()
        db.create_all()
        user = User(username="alice", password_hash=generate_password_hash("wonderland"))
        db.session.add(user)
        db.session.commit()
    return app


def test_docs_login_with_user_credentials():
    app = auth_app()
    client = app.test_client()

    resp = client.get("/docs")
    assert resp.status_code == 200
    assert b"API Documentation Login" in resp.data

    resp = client.post(
        "/docs",
        data={"username": "alice", "password": "wonderland"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"API Documentation Login" not in resp.data
