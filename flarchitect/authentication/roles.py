"""Role-based access control decorators."""

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from flask import request

from flarchitect.authorization.roles import _resolve_required_roles
from flarchitect.authentication.user import get_current_user
from flarchitect.exceptions import CustomHTTPException

F = TypeVar("F", bound=Callable[..., Any])


def require_roles(*roles: str, any_of: bool = False) -> Callable[[F], F]:
    """Enforce role-based access on the decorated function.

    Why/How:
        Validates that the authenticated user exposes required roles on
        ``current_user.roles``. When ``any_of`` is True, possession of any
        listed role is sufficient; otherwise all roles are required.

    Args:
        *roles: Role names to check against ``current_user.roles``.
        any_of: When True, allow access if any role matches; when False, all
            roles must be present.

    Returns:
        A decorator enforcing the role check.

    Raises:
        CustomHTTPException: 401 when unauthenticated, 403 when roles do not
            satisfy the requirement.
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
                    return _forbidden_with_context(
                        provided_roles=list(user_roles),
                        required_roles=list(required),
                        any_of=any_of,
                        reason="missing_roles",
                    )
                if not any_of and not required.issubset(user_roles):
                    return _forbidden_with_context(
                        provided_roles=list(user_roles),
                        required_roles=list(required),
                        any_of=any_of,
                        reason="missing_roles",
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
    """Backward compatible wrapper requiring all listed roles.

    Why/How:
        Alias for :func:`require_roles` configured with ``any_of=False`` for
        readability when all roles are mandatory.
    """

    return require_roles(*roles)


def roles_accepted(*roles: str) -> Callable[[F], F]:
    """Backward compatible wrapper requiring any of the listed roles.

    Why/How:
        Alias for :func:`require_roles` configured with ``any_of=True``.
    """

    return require_roles(*roles, any_of=True)


__all__ = ["require_roles", "roles_required", "roles_accepted"]


# ----- Local helpers -----
def _build_user_context() -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Best-effort user info and lookup context from request/app state.

    Returns:
        tuple[user_dict | None, lookup_dict | None]
    """
    user_obj = get_current_user()
    user_dict: dict[str, Any] | None = None
    lookup_dict: dict[str, Any] | None = None

    # Try to enrich using get_pk_and_lookups from JWT helpers
    try:  # Optional import; tests should pass if missing
        from flarchitect.authentication.jwt import get_pk_and_lookups

        pk_field, lookup_field = get_pk_and_lookups()
    except Exception:  # pragma: no cover - optional path
        pk_field, lookup_field = None, None

    # If no user in context, optionally try to decode from Authorization header
    if user_obj is None:
        try:  # Optional import
            from flarchitect.authentication.jwt import get_user_from_token
            from flask import request as _rq

            auth = _rq.headers.get("Authorization")
            if auth and auth.lower().startswith("bearer "):
                token = auth.split(" ", 1)[1]
                user_obj = get_user_from_token(token, secret_key=None)
        except Exception:  # pragma: no cover - best-effort
            user_obj = None

    if user_obj is not None:
        roles = list(getattr(user_obj, "roles", []) or [])
        # Attempt id/username using the lookup hints
        user_id = getattr(user_obj, pk_field, None) if pk_field else getattr(user_obj, "id", None)
        username = getattr(user_obj, lookup_field, None) if lookup_field else getattr(user_obj, "username", None)
        user_dict = {"id": user_id, "username": username, "roles": roles}

        if pk_field or lookup_field:
            lookup_dict = {
                "pk": getattr(user_obj, pk_field, None) if pk_field else None,
                "lookups": ({lookup_field: getattr(user_obj, lookup_field, None)} if lookup_field else {}),
            }

    return user_dict, lookup_dict


def _infer_resource_from_path() -> str | None:
    """Derive a best-effort resource identifier from the request path."""
    try:
        from flarchitect.utils.config_helpers import get_config_or_model_meta

        api_prefix = get_config_or_model_meta("API_PREFIX", default="/api") or "/api"
    except Exception:  # pragma: no cover - fallback
        api_prefix = "/api"

    try:
        path = request.path or ""
        if path.startswith(api_prefix):
            remainder = path[len(api_prefix) :].lstrip("/")
            # First path segment is typically the resource name
            return remainder.split("/", 1)[0] or None
        # Fallback to endpoint suffix
        return (request.endpoint or "").split(".")[-1] or None
    except Exception:  # pragma: no cover - outside request context
        return None


def _forbidden_with_context(
    *,
    provided_roles: list[str] | None,
    required_roles: list[str] | None,
    any_of: bool,
    reason: str,
):
    """Return a 403 response enriched with role/config context.

    Falls back to ``CustomHTTPException`` when helpers are unavailable.
    """
    # Prefer required roles resolved from API_ROLE_MAP; fall back to decorator args
    try:
        resolved_roles, resolved_any_of, resolved_from = _resolve_required_roles(request.method)
        if resolved_roles is not None:
            required_roles = resolved_roles
            any_of = resolved_any_of
    except Exception:  # pragma: no cover - resolver unavailable
        resolved_from = None

    # Gather user context
    user_ctx, lookup_ctx = _build_user_context()

    # Safely access request attributes when within a request context
    try:
        req_method = request.method
        req_path = request.path
    except Exception:  # pragma: no cover - outside request context
        req_method, req_path = None, None

    payload = {
        "error": "forbidden",
        "message": "Missing required role(s) for this action.",
        "required_roles": required_roles,
        "any_of": bool(any_of),
        "method": req_method,
        "path": req_path,
        "resource": _infer_resource_from_path(),
        "user": user_ctx,
        "lookup": lookup_ctx,
        "resolved_from": resolved_from if 'resolved_from' in locals() else None,
        "reason": reason,
    }

    # Use create_response when available to preserve library envelope
    try:
        from flarchitect.utils.response_helpers import create_response

        return create_response(status=403, errors=payload)
    except Exception:  # pragma: no cover - fallback to existing behaviour
        raise CustomHTTPException(status_code=403, reason="Insufficient role")
