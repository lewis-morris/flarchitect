# auth.py
"""Utilities for managing user context within requests.

These helpers wrap a :class:`contextvars.ContextVar` to provide a global-like
interface for accessing the current user while remaining thread-safe.
"""

from contextvars import ContextVar
from typing import Any

from werkzeug.local import LocalProxy

# Create a ContextVar to store the current user
_current_user_ctx_var: ContextVar[Any] = ContextVar("current_user", default=None)


def set_current_user(user: Any) -> None:
    """Store the given user in the context.

    Args:
        user (Any): The user object to place into context. ``None`` clears the
            current user.

    Returns:
        None: This function does not return a value.
    """

    _current_user_ctx_var.set(user)


def get_current_user() -> Any | None:
    """Retrieve the user stored in the context.

    Returns:
        Any | None: The current user if one has been set, otherwise ``None``.
    """

    return _current_user_ctx_var.get()


# Create a LocalProxy to access the current user easily
current_user = LocalProxy(get_current_user)
