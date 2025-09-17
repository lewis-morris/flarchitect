"""Helpers for resolving and normalising role specifications.

These helpers provide a consistent way to interpret role requirements from
configuration and to expose the resolved policy to callers.
"""

from __future__ import annotations

from typing import Any, Tuple

try:  # Flask optional import guard for typing/runtime access
    from flask import current_app
except Exception:  # pragma: no cover - Flask not available in some contexts
    current_app = None  # type: ignore[assignment]


def _normalize_roles_spec(spec: Any) -> tuple[list[str] | None, bool]:
    """Normalise a roles spec to (roles, any_of).

    Supported shapes:
    - None, True -> (None, False) meaning no explicit roles required.
    - str -> ([str], False)
    - list|tuple[str] -> (list[str], False)
    - dict with {"roles": str|list[str], "any_of": bool} -> (list[str]|None, bool)

    Args:
        spec: Arbitrary role spec from configuration or code.

    Returns:
        tuple[list[str] | None, bool]: A tuple of the concrete role list or
            ``None`` when no explicit roles are required, and an ``any_of``
            boolean indicating matching semantics.
    """
    # No explicit role requirement
    if spec is None:
        return None, False
    if spec is True:
        # Treated as "auth only" in some contexts; keep consistent here
        return None, False

    # Simple forms
    if isinstance(spec, str):
        return [spec], False
    if isinstance(spec, (list, tuple)):
        return [str(r) for r in spec], False

    # Dict form with optional any_of
    if isinstance(spec, dict):
        roles = spec.get("roles")
        any_of = bool(spec.get("any_of", False))
        if roles is None or roles is True:
            return None, any_of
        if isinstance(roles, str):
            return [roles], any_of
        if isinstance(roles, (list, tuple)):
            return [str(r) for r in roles], any_of
        return None, any_of

    # Unknown type: safest is no explicit roles (maintain behaviour)
    return None, False


def _resolve_required_roles(method: str) -> tuple[list[str] | None, bool, str | None]:
    """Resolve required roles for the given HTTP method.

    Detection order (first match wins):
    - "GET" (only when method == "GET")
    - exact method (e.g., "POST")
    - "ALL"
    - "*"

    The configuration may be:
    - A single spec (str | list[str] | dict) applied to all methods.
    - A mapping of method keys to the above spec shapes.

    Args:
        method: HTTP method (e.g., "GET", "POST").

    Returns:
        tuple[list[str] | None, bool, str | None]: (roles, any_of, resolved_from)
        where ``resolved_from`` is the matched key or ``None`` when no mapping
        could be resolved.
    """
    resolved_from: str | None = None

    try:
        role_map = (current_app and current_app.config.get("API_ROLE_MAP")) or None  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover - outside app context
        role_map = None

    # Single spec applied to all
    if role_map is not None and not isinstance(role_map, dict):
        roles, any_of = _normalize_roles_spec(role_map)
        return roles, any_of, "*"

    if isinstance(role_map, dict):
        method = (method or "").upper()
        keys: list[str] = []
        if method == "GET":
            keys.append("GET")
        keys.extend([method, "ALL", "*"])

        for k in keys:
            if k in role_map:
                resolved_from = k
                roles, any_of = _normalize_roles_spec(role_map[k])
                return roles, any_of, resolved_from

    # No mapping found; maintain previous behaviour of the caller (None)
    return None, False, None


__all__ = ["_normalize_roles_spec", "_resolve_required_roles"]

