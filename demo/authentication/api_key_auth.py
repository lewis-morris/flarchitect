"""API key authentication example."""

from __future__ import annotations

from demo.authentication.app_base import BaseConfig, User, create_app
from flarchitect.authentication.user import get_current_user, set_current_user


def lookup_user_by_token(token: str) -> User | None:
    """Return a user matching ``token``.

    Args:
        token (str): Raw API key supplied by the client.

    Returns:
        User | None: Matching user or ``None`` if the token is invalid.
    """

    user = User.query.filter_by(api_key=token).first()
    if user:
        # When a match is found, store the user in the request context so later
        # handlers can access it via ``get_current_user``.
        set_current_user(user)
    return user


class Config(BaseConfig):
    """Configuration for the API key authentication demo.

    Attributes:
        API_AUTHENTICATE_METHOD (list[str]): Enabled authentication strategies.
        API_KEY_AUTH_AND_RETURN_METHOD (Callable): Function used to resolve a
            user from an API key.
    """

    API_AUTHENTICATE_METHOD = ["api_key"]
    API_KEY_AUTH_AND_RETURN_METHOD = staticmethod(lookup_user_by_token)
    API_USER_MODEL = User


app = create_app(Config)


@app.get("/profile")
def profile() -> dict[str, str]:
    """Return the current user's profile.

    Returns:
        dict[str, str]: The authenticated user's username.
    """

    user = get_current_user()
    return {"username": user.username}
