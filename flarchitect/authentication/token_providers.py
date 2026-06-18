"""Helpers for extracting authentication tokens from incoming requests."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from flask import Request, request
from werkzeug.utils import import_string

from flarchitect.utils.config_helpers import get_config_or_model_meta

ProviderFunc = Callable[[Request], str | None]

DEFAULT_TOKEN_PROVIDERS = ("header",)
DEFAULT_AUTH_COOKIE_NAME = "access_token"


def _header_provider(req: Request) -> str | None:
    """Extract a Bearer token from the ``Authorization`` header."""

    auth = req.headers.get("Authorization")
    if not auth:
        return None
    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip() or None


def _cookie_provider(req: Request, cookie_name: str) -> str | None:
    """Extract a token from a cookie."""

    token = req.cookies.get(cookie_name)
    return token.strip() if isinstance(token, str) and token.strip() else None


def _named_provider(name: str, provider: ProviderFunc) -> ProviderFunc:
    """Attach a useful name to dynamically-created providers."""

    provider.__name__ = name
    return provider


def _normalise_provider(provider: Any, *, cookie_name: str) -> ProviderFunc:
    """Resolve a provider spec into a callable."""

    if callable(provider):
        return provider

    if isinstance(provider, str):
        key = provider.strip().lower()
        if key == "header":
            return _header_provider
        if key == "cookie":
            return _named_provider("cookie", lambda req: _cookie_provider(req, cookie_name))

        # Allow dotted import path
        try:
            imported = import_string(provider)
            if callable(imported):
                return imported
        except Exception:  # pragma: no cover - optional path
            raise ValueError(f"Unable to import auth token provider '{provider}'") from None

    raise ValueError(f"Unsupported auth token provider specification: {provider!r}")


def _provider_config_context(
    *,
    model: Any | None = None,
    output_schema: Any | None = None,
    input_schema: Any | None = None,
    method: str | None = None,
) -> dict[str, Any]:
    """Build the common config lookup context for token provider settings."""

    return {
        "model": model,
        "output_schema": output_schema,
        "input_schema": input_schema,
        "method": method,
    }


def _coerce_provider_specs(config: Any) -> list[Any]:
    """Return a list of provider specs from config."""

    if config is None:
        return list(DEFAULT_TOKEN_PROVIDERS)
    if isinstance(config, (str, bytes)) or not isinstance(config, Iterable):
        return [config]
    return list(config)


def _normalise_token(token: Any) -> str | None:
    """Return a non-empty token string from provider output."""

    if not isinstance(token, str):
        return None
    token = token.strip()
    return token or None


def _provider_name(provider: ProviderFunc) -> str:
    """Return a stable provider identifier for diagnostics."""

    return getattr(provider, "__name__", provider.__class__.__name__)


def resolve_token_providers(
    *,
    model: Any | None = None,
    output_schema: Any | None = None,
    input_schema: Any | None = None,
    method: str | None = None,
) -> list[ProviderFunc]:
    """Return configured token providers for the current context."""

    context = _provider_config_context(
        model=model,
        output_schema=output_schema,
        input_schema=input_schema,
        method=method,
    )
    config = get_config_or_model_meta(
        "API_AUTH_TOKEN_PROVIDERS",
        **context,
        default=None,
    )
    cookie_name = get_config_or_model_meta(
        "API_AUTH_COOKIE_NAME",
        **context,
        default=DEFAULT_AUTH_COOKIE_NAME,
    )

    return [_normalise_provider(item, cookie_name=str(cookie_name)) for item in _coerce_provider_specs(config)]


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
            token = _normalise_token(provider(req))
        except Exception:  # pragma: no cover - providers must be defensive
            continue
        if token:
            return token, _provider_name(provider)
    return None, None


def extract_token_from_cookie(cookie_name: str | None = None, req: Request | None = None) -> str | None:
    """Convenience helper to pull a token from a cookie on the current request."""

    req = req or request
    name = cookie_name or get_config_or_model_meta("API_AUTH_COOKIE_NAME", default=DEFAULT_AUTH_COOKIE_NAME)
    return _cookie_provider(req, str(name))


__all__ = [
    "extract_token_from_cookie",
    "extract_token_from_request",
    "resolve_token_providers",
]
