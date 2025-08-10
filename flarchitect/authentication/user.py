# auth.py
from contextvars import ContextVar

from werkzeug.local import LocalProxy

# Create a ContextVar to store the current user
_current_user_ctx_var = ContextVar("current_user", default=None)


def set_current_user(user):
    """Set the current user in the context."""
    _current_user_ctx_var.set(user)


def get_current_user():
    """Get the current user from the context."""
    return _current_user_ctx_var.get()


# Create a LocalProxy to access the current user easily
current_user = LocalProxy(get_current_user)
