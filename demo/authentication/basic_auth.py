"""HTTP Basic authentication example."""

from __future__ import annotations

from demo.authentication.app_base import BaseConfig, User, create_app, schema
from flarchitect.authentication.user import get_current_user


class Config(BaseConfig):
    API_AUTHENTICATE_METHOD = ["basic"]
    API_USER_MODEL = User
    API_USER_LOOKUP_FIELD = "username"
    API_CREDENTIAL_CHECK_METHOD = "check_password"


app = create_app(Config)


@app.get("/profile")
@schema.route(model=User)
def profile() -> dict[str, str]:
    """Return the current user's profile."""

    user = get_current_user()
    return {"username": user.username}
