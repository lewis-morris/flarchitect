from __future__ import annotations

import importlib
import pkgutil
from types import ModuleType

import flarchitect as pkg


def test_import_all_flarchitect_modules() -> None:
    """Import every submodule to ensure they load without side effects/errors."""

    seen: list[str] = []
    errors: list[str] = []

    for mod in pkgutil.walk_packages(pkg.__path__, prefix=pkg.__name__ + "."):
        name = mod.name
        seen.append(name)
        try:
            imported: ModuleType = importlib.import_module(name)
            assert imported is not None  # pragma: no cover - defensive
        except Exception as exc:  # pragma: no cover - report exact offender
            errors.append(f"{name}: {exc!r}")

    # If any import failed, surface them
    assert not errors, "\n".join(errors)

