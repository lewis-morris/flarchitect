"""JWT authentication example."""

from __future__ import annotations

from flask import request

from demo.authentication.app_base import BaseConfig, User, create_app
from flarchitect.authentication.jwt import generate_access_token, generate_refresh_token
from flarchitect.authentication.user import get_current_user
from flarchitect.exceptions import CustomHTTPException


class Config(BaseConfig):
    """Configuration for the JWT authentication demo.

    Attributes:
        API_AUTHENTICATE_METHOD (list[str]): Enabled authentication strategies.
        ACCESS_SECRET_KEY (str): Secret key used to sign access tokens.
        REFRESH_SECRET_KEY (str): Secret key used to sign refresh tokens.
        API_USER_MODEL (type[User]): Model used to authenticate users.
        API_USER_LOOKUP_FIELD (str): Field used to look up users by credential.
        API_CREDENTIAL_CHECK_METHOD (str): Name of the method that validates a
            user's password.
    """

    API_AUTHENTICATE_METHOD = ["jwt"]
    ACCESS_SECRET_KEY = "access-secret"
    REFRESH_SECRET_KEY = "refresh-secret"
    API_USER_MODEL = User
    API_USER_LOOKUP_FIELD = "username"
    API_CREDENTIAL_CHECK_METHOD = "check_password"


app = create_app(Config)


@app.post("/jwt-login")
def login() -> dict[str, str]:
    """Authenticate the user and issue JWT tokens.

    Returns:
        dict[str, str]: A pair of ``access_token`` and ``refresh_token`` strings.

    Raises:
        CustomHTTPException: If the provided credentials are invalid.
    """

    data = request.get_json() or {}
    # Look up the user by username; passwords are stored in plain text purely
    # for demonstration. Real applications should hash and salt passwords.
    user = User.query.filter_by(username=data.get("username")).first()
    if not user or not user.check_password(data.get("password", "")):
        raise CustomHTTPException(status_code=401)
    return {
        "access_token": generate_access_token(user),
        "refresh_token": generate_refresh_token(user),
    }


@app.get("/profile")
def profile() -> dict[str, str]:
    """Return the current user's profile.

    Returns:
        dict[str, str]: The authenticated user's username.
    """

    user = get_current_user()
    return {"username": user.username}
