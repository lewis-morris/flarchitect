"""Convenience authentication helpers."""

from __future__ import annotations

from typing import Any

from flask import request

from flarchitect.authentication.jwt import get_user_from_token
from flarchitect.authentication.token_providers import extract_token_from_cookie
from flarchitect.authentication.user import set_current_user


def load_user_from_cookie(cookie_name: str | None = None) -> bool:
    """Populate ``current_user`` from a JWT stored in a cookie.

    Args:
        cookie_name: Optional cookie name. Defaults to
            ``API_AUTH_COOKIE_NAME`` (``"access_token"``).

    Returns:
        True when a user was loaded successfully, otherwise False.
    """

    token = extract_token_from_cookie(cookie_name, request)
    if not token:
        return False

    user = get_user_from_token(token, secret_key=None)
    if not user:
        return False

    set_current_user(user)
    return True


__all__ = ["load_user_from_cookie"]
