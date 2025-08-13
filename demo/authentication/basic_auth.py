"""HTTP Basic authentication example."""

from __future__ import annotations

from demo.authentication.app_base import BaseConfig, User, create_app
from flarchitect.authentication.user import get_current_user


class Config(BaseConfig):
    """Configuration for the HTTP Basic authentication demo.

    Attributes:
        API_AUTHENTICATE_METHOD (list[str]): Enabled authentication strategies.
        API_USER_MODEL (type[User]): Model used for authentication.
        API_USER_LOOKUP_FIELD (str): Attribute used to locate a user.
        API_CREDENTIAL_CHECK_METHOD (str): Name of the method that validates the
            supplied password.
    """

    API_AUTHENTICATE_METHOD = ["basic"]
    API_USER_MODEL = User
    API_USER_LOOKUP_FIELD = "username"
    API_CREDENTIAL_CHECK_METHOD = "check_password"


app = create_app(Config)


@app.get("/profile")
def profile() -> dict[str, str]:
    """Return the current user's profile.

    Returns:
        dict[str, str]: The authenticated user's username.
    """

    # The ``Authorization`` header is parsed automatically by flarchitect's
    # built-in basic authentication handler.
    user = get_current_user()
    return {"username": user.username}
