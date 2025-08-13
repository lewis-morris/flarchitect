"""OpenAPI specification generation and helper utilities."""

from importlib import import_module
from typing import Any

__all__ = ["CustomSpec", "register_routes_with_spec", "register_schemas"]


def __getattr__(name: str) -> Any:  # pragma: no cover - simple proxy
    if name in __all__:
        module = import_module("flarchitect.specs.generator")
        return getattr(module, name)
    raise AttributeError(f"module {__name__} has no attribute {name}")
