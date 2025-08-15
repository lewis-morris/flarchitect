"""Role-based access control decorators."""

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from flarchitect.authentication.user import get_current_user
from flarchitect.exceptions import CustomHTTPException

F = TypeVar("F", bound=Callable[..., Any])


def require_roles(*roles: str, any_of: bool = False) -> Callable[[F], F]:
    """Enforce role-based access on the decorated function.

    Args:
        *roles: Role names to validate against ``current_user.roles``.
        any_of: When ``True`` any listed role grants access. Defaults to
            ``False`` requiring *all* roles.

    Returns:
        Callable[[F], F]: A decorator enforcing the role check.

    Raises:
        CustomHTTPException: ``401`` when no user is authenticated or ``403``
            when roles do not match.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            user = get_current_user()
            if user is None:
                raise CustomHTTPException(
                    status_code=401,
                    reason="Authentication required",
                )

            user_roles = set(getattr(user, "roles", []) or [])
            required = set(roles)

            if required:
                if any_of and not required.intersection(user_roles):
                    raise CustomHTTPException(
                        status_code=403,
                        reason="Insufficient role",
                    )
                if not any_of and not required.issubset(user_roles):
                    raise CustomHTTPException(
                        status_code=403,
                        reason="Insufficient role",
                    )

            return func(*args, **kwargs)

        if not hasattr(wrapper, "_decorators"):
            wrapper._decorators = []  # type: ignore[attr-defined]
        decorator.__name__ = "require_roles"
        decorator._args = roles  # type: ignore[attr-defined]
        decorator._any_of = any_of  # type: ignore[attr-defined]
        wrapper._decorators.append(decorator)  # type: ignore[attr-defined]

        return cast(F, wrapper)

    return decorator


def roles_required(*roles: str) -> Callable[[F], F]:
    """Backward compatible wrapper requiring all listed roles."""

    return require_roles(*roles)


def roles_accepted(*roles: str) -> Callable[[F], F]:
    """Backward compatible wrapper requiring any of the listed roles."""

    return require_roles(*roles, any_of=True)


__all__ = ["require_roles", "roles_required", "roles_accepted"]
