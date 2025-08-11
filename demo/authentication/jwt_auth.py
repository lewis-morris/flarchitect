"""JWT authentication example."""

from __future__ import annotations

from flask import request

from demo.authentication.app_base import BaseConfig, User, create_app, schema
from flarchitect.authentication.jwt import generate_access_token, generate_refresh_token
from flarchitect.authentication.user import get_current_user
from flarchitect.exceptions import CustomHTTPException


class Config(BaseConfig):
    API_AUTHENTICATE_METHOD = ["jwt"]
    ACCESS_SECRET_KEY = "access-secret"
    REFRESH_SECRET_KEY = "refresh-secret"
    API_USER_MODEL = User
    API_USER_LOOKUP_FIELD = "username"
    API_CREDENTIAL_CHECK_METHOD = "check_password"


app = create_app(Config)


@app.post("/auth/login")
@schema.route(model=User, auth=False)
def login() -> dict[str, str]:
    """Authenticate the user and issue JWT tokens."""

    data = request.get_json() or {}
    user = User.query.filter_by(username=data.get("username")).first()
    if not user or not user.check_password(data.get("password", "")):
        raise CustomHTTPException(status_code=401)
    return {
        "access_token": generate_access_token(user),
        "refresh_token": generate_refresh_token(user),
    }


@app.get("/profile")
@schema.route(model=User)
def profile() -> dict[str, str]:
    """Return the current user's profile."""

    user = get_current_user()
    return {"username": user.username}
