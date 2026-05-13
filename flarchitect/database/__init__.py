"""Database helpers providing CRUD services and SQLAlchemy utilities.

The package exposes selected attributes lazily so importing ``flarchitect`` at
module import time does not trigger circular dependencies between
``flarchitect.core`` and ``flarchitect.database``.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_EXPORTED = {
    "CrudService",
    "apply_sorting_to_query",
    "get_model_columns",
    "get_model_relationships",
    "paginate_query",
}


def __getattr__(name: str) -> Any:
    """Lazily resolve attributes from :mod:`flarchitect.database.operations`."""

    if name in _EXPORTED:
        module = import_module(".operations", __name__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:  # pragma: no cover - trivial
    return sorted(set(globals()) | _EXPORTED)


__all__ = sorted(_EXPORTED)
