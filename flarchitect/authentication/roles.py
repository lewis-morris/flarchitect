from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from flarchitect.authentication.user import current_user
from flarchitect.exceptions import CustomHTTPException

F = TypeVar("F", bound=Callable[..., Any])


def roles_required(*roles: str) -> Callable[[F], F]:
    """Restrict access to users possessing specific roles.

    Args:
        *roles: Variable length argument list of role names required to access
            the decorated endpoint.

    Returns:
        Callable[[F], F]: A decorator enforcing role-based access control.

    Raises:
        CustomHTTPException: Raised with status code ``403`` when the current
            user lacks any of the required roles or no user is authenticated.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            user_roles = getattr(current_user, "roles", None)
            if user_roles is None:
                raise CustomHTTPException(status_code=403, reason="Roles required")

            if roles and not set(roles).issubset(set(user_roles)):
                raise CustomHTTPException(status_code=403, reason="Roles required")

            return func(*args, **kwargs)

        if not hasattr(wrapper, "_decorators"):
            wrapper._decorators = []  # type: ignore[attr-defined]
        decorator.__name__ = "roles_required"
        decorator._args = roles  # type: ignore[attr-defined]
        wrapper._decorators.append(decorator)  # type: ignore[attr-defined]

        return cast(F, wrapper)

    return decorator
