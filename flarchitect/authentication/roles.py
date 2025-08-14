from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from flarchitect.authentication.user import get_current_user
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
        CustomHTTPException: Raised with status code ``401`` when no user is
            authenticated or ``403`` when the user lacks the required roles.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            user = get_current_user()
            if user is None:
                raise CustomHTTPException(
                    status_code=401, reason="Authentication required"
                )

            user_roles = getattr(user, "roles", None)
            if roles and not set(roles).issubset(set(user_roles or [])):
                raise CustomHTTPException(status_code=403, reason="Insufficient role")

            return func(*args, **kwargs)

        if not hasattr(wrapper, "_decorators"):
            wrapper._decorators = []  # type: ignore[attr-defined]
        decorator.__name__ = "roles_required"
        decorator._args = roles  # type: ignore[attr-defined]
        wrapper._decorators.append(decorator)  # type: ignore[attr-defined]

        return cast(F, wrapper)

    return decorator


def roles_accepted(*roles: str) -> Callable[[F], F]:
    """Allow access when the user has any matching role.

    Args:
        *roles: Variable length argument list of role names any of which
            will grant access to the decorated endpoint.

    Returns:
        Callable[[F], F]: A decorator enforcing role-based access control.

    Raises:
        CustomHTTPException: Raised with status code ``401`` when no user is
            authenticated or ``403`` when the user lacks all provided roles.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            user = get_current_user()
            if user is None:
                raise CustomHTTPException(
                    status_code=401, reason="Authentication required"
                )

            user_roles = getattr(user, "roles", None)
            if roles and not set(roles).intersection(set(user_roles or [])):
                raise CustomHTTPException(status_code=403, reason="Insufficient role")

            return func(*args, **kwargs)

        if not hasattr(wrapper, "_decorators"):
            wrapper._decorators = []  # type: ignore[attr-defined]
        decorator.__name__ = "roles_accepted"
        decorator._args = roles  # type: ignore[attr-defined]
        wrapper._decorators.append(decorator)  # type: ignore[attr-defined]

        return cast(F, wrapper)

    return decorator
