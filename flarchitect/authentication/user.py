# auth.py
"""Utilities for managing user context within requests.

These helpers wrap a :class:`contextvars.ContextVar` to provide a global-like
interface for accessing the current user while remaining thread-safe.
"""

from contextvars import ContextVar
from typing import Any

from flask import Flask
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


def register_user_teardown(app: Flask) -> None:
    """Register a teardown handler to clear the current user.

    Args:
        app (Flask): The Flask application instance.

    Returns:
        None: This function does not return a value.
    """

    if getattr(app, "_flarchitect_user_teardown_registered", False):
        return
    app._flarchitect_user_teardown_registered = True

    @app.teardown_request
    def _clear_current_user(exception: BaseException | None = None) -> None:
        """Remove the user from context after each request.

        Args:
            exception (BaseException | None): Exception during the request, if any.

        Returns:
            None: Flask ignores the return value of teardown callbacks.
        """

        set_current_user(None)


# Create a LocalProxy to access the current user easily
current_user = LocalProxy(get_current_user)
