"""Custom authentication example."""

from __future__ import annotations

from flask import request

from demo.authentication.app_base import BaseConfig, User, create_app, schema
from flarchitect.authentication.user import get_current_user, set_current_user


def custom_auth() -> bool:
    """Authenticate based on an ``X-Token`` header."""

    token = request.headers.get("X-Token", "")
    user = User.query.filter_by(api_key=token).first()
    if user:
        set_current_user(user)
        return True
    return False


class Config(BaseConfig):
    API_AUTHENTICATE_METHOD = ["custom"]
    API_CUSTOM_AUTH = staticmethod(custom_auth)


app = create_app(Config)


@app.get("/profile")
@schema.route(model=User)
def profile() -> dict[str, str]:
    """Return the current user's profile."""

    user = get_current_user()
    return {"username": user.username}
