"""API key authentication example."""

from __future__ import annotations

from demo.authentication.app_base import BaseConfig, User, create_app, schema
from flarchitect.authentication.user import get_current_user, set_current_user


def lookup_user_by_token(token: str) -> User | None:
    """Return a user matching ``token``."""

    user = User.query.filter_by(api_key=token).first()
    if user:
        set_current_user(user)
    return user


class Config(BaseConfig):
    API_AUTHENTICATE_METHOD = ["api_key"]
    API_KEY_AUTH_AND_RETURN_METHOD = staticmethod(lookup_user_by_token)


app = create_app(Config)


@app.get("/profile")
@schema.route(model=User)
def profile() -> dict[str, str]:
    """Return the current user's profile."""

    user = get_current_user()
    return {"username": user.username}
