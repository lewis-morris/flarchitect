"""Helpers for extracting authentication tokens from incoming requests."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from flask import Request, request
from werkzeug.utils import import_string

from flarchitect.utils.config_helpers import get_config_or_model_meta

ProviderFunc = Callable[[Request], str | None]


def _header_provider(req: Request) -> str | None:
    """Extract a Bearer token from the ``Authorization`` header."""

    auth = req.headers.get("Authorization")
    if not auth:
        return None
    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1]


def _cookie_provider(req: Request, cookie_name: str) -> str | None:
    """Extract a token from a cookie."""

    token = req.cookies.get(cookie_name)
    return token.strip() if isinstance(token, str) and token.strip() else None


def _normalise_provider(provider: Any, *, cookie_name: str) -> ProviderFunc:
    """Resolve a provider spec into a callable."""

    if callable(provider):
        return provider

    if isinstance(provider, str):
        key = provider.strip().lower()
        if key == "header":
            return _header_provider
        if key == "cookie":
            return lambda req: _cookie_provider(req, cookie_name)

        # Allow dotted import path
        try:
            imported = import_string(provider)
            if callable(imported):
                return imported
        except Exception:  # pragma: no cover - optional path
            raise ValueError(f"Unable to import auth token provider '{provider}'") from None

    raise ValueError(f"Unsupported auth token provider specification: {provider!r}")


def resolve_token_providers(
    *,
    model: Any | None = None,
    output_schema: Any | None = None,
    input_schema: Any | None = None,
    method: str | None = None,
) -> list[ProviderFunc]:
    """Return configured token providers for the current context."""

    config = get_config_or_model_meta(
        "API_AUTH_TOKEN_PROVIDERS",
        model=model,
        output_schema=output_schema,
        input_schema=input_schema,
        method=method,
        default=None,
    )

    if config is None:
        config = ["header"]
    elif isinstance(config, (str, bytes)):
        config = [config]
    elif not isinstance(config, Iterable):
        config = [config]

    cookie_name = get_config_or_model_meta(
        "API_AUTH_COOKIE_NAME",
        model=model,
        output_schema=output_schema,
        input_schema=input_schema,
        method=method,
        default="access_token",
    )

    providers: list[ProviderFunc] = []
    for item in config:
        providers.append(_normalise_provider(item, cookie_name=str(cookie_name)))

    return providers


def extract_token_from_request(
    *,
    model: Any | None = None,
    output_schema: Any | None = None,
    input_schema: Any | None = None,
    method: str | None = None,
) -> tuple[str | None, str | None]:
    """Iterate providers and return the first non-empty token."""

    req = request
    for provider in resolve_token_providers(
        model=model,
        output_schema=output_schema,
        input_schema=input_schema,
        method=method,
    ):
        try:
            token = provider(req)
        except Exception:  # pragma: no cover - providers must be defensive
            continue
        if token:
            return token, getattr(provider, "__name__", provider.__class__.__name__)
    return None, None


def extract_token_from_cookie(cookie_name: str | None = None, req: Request | None = None) -> str | None:
    """Convenience helper to pull a token from a cookie on the current request."""

    req = req or request
    name = cookie_name or get_config_or_model_meta("API_AUTH_COOKIE_NAME", default="access_token")
    return _cookie_provider(req, str(name))


__all__ = [
    "resolve_token_providers",
    "extract_token_from_request",
    "extract_token_from_cookie",
]
