from __future__ import annotations

import contextlib
from collections.abc import Callable
from typing import Any

from flask import Request, Response


class PluginBase:
    """Base class for flarchitect plugins.

    Implement any of the hook methods to observe or influence behaviour.
    All hooks are optional. Default implementations are no-ops.

    Stable hook signatures (kwargs may grow but not change meaning):
    - request_started(request: Request) -> None
    - request_finished(request: Request, response: Response) -> Response | None
    - before_authenticate(context: dict[str, Any]) -> dict[str, Any] | None
    - after_authenticate(context: dict[str, Any], success: bool, user: Any | None) -> None
    - before_model_op(context: dict[str, Any]) -> dict[str, Any] | None
    - after_model_op(context: dict[str, Any], output: Any) -> Any | None
    - spec_build_started(spec: Any) -> None
    - spec_build_completed(spec_dict: dict[str, Any]) -> dict[str, Any] | None
    """

    def request_started(self, request: Request) -> None:  # pragma: no cover - default no-op
        return None

    def request_finished(self, request: Request, response: Response) -> Response | None:  # pragma: no cover - default no-op
        return None

    def before_authenticate(self, context: dict[str, Any]) -> dict[str, Any] | None:  # pragma: no cover - default no-op
        return None

    def after_authenticate(self, context: dict[str, Any], success: bool, user: Any | None) -> None:  # pragma: no cover - default no-op
        return None

    def before_model_op(self, context: dict[str, Any]) -> dict[str, Any] | None:  # pragma: no cover - default no-op
        return None

    def after_model_op(self, context: dict[str, Any], output: Any) -> Any | None:  # pragma: no cover - default no-op
        return None

    def spec_build_started(self, spec: Any) -> None:  # pragma: no cover - default no-op
        return None

    def spec_build_completed(self, spec_dict: dict[str, Any]) -> dict[str, Any] | None:  # pragma: no cover - default no-op
        return None


class PluginManager:
    """Manage registration and invocation of flarchitect plugins."""

    def __init__(self, plugins: list[PluginBase] | None = None) -> None:
        self._plugins: list[PluginBase] = plugins or []

    @staticmethod
    def _coerce(entry: Any) -> PluginBase:
        # Support instances or classes; ignore invalid entries gracefully
        if isinstance(entry, PluginBase):
            return entry
        if isinstance(entry, type) and issubclass(entry, PluginBase):
            return entry()  # type: ignore[call-arg]
        # Try callables returning a PluginBase
        if callable(entry):
            candidate = entry()
            if isinstance(candidate, PluginBase):
                return candidate
        raise TypeError("Invalid plugin entry; expected PluginBase or factory")

    @classmethod
    def from_config(cls, config_val: Any) -> PluginManager:
        plugins: list[PluginBase] = []
        if isinstance(config_val, list):
            for entry in config_val:
                try:
                    plugins.append(cls._coerce(entry))
                except Exception:
                    # Skip invalid plugins rather than breaking app startup
                    continue
        elif config_val:
            with contextlib.suppress(Exception):
                plugins.append(cls._coerce(config_val))
        return cls(plugins)

    # Dispatch helpers
    def _first_non_none(self, func: Callable[[PluginBase], Any]) -> Any:
        for p in self._plugins:
            result = func(p)
            if result is not None:
                return result
        return None

    def request_started(self, request: Request) -> None:
        for p in self._plugins:
            try:
                p.request_started(request)
            except Exception:
                continue

    def request_finished(self, request: Request, response: Response) -> Response | None:
        return self._first_non_none(lambda p: self._safe_call(p.request_finished, request, response))

    def before_authenticate(self, context: dict[str, Any]) -> dict[str, Any] | None:
        updates: dict[str, Any] | None = None
        for p in self._plugins:
            try:
                upd = p.before_authenticate(context)
                if isinstance(upd, dict):
                    context.update(upd)
                    updates = context
            except Exception:
                continue
        return updates

    def after_authenticate(self, context: dict[str, Any], success: bool, user: Any | None) -> None:
        for p in self._plugins:
            with contextlib.suppress(Exception):
                p.after_authenticate(context, success, user)

    def before_model_op(self, context: dict[str, Any]) -> dict[str, Any] | None:
        updates: dict[str, Any] | None = None
        for p in self._plugins:
            try:
                upd = p.before_model_op(context)
                if isinstance(upd, dict):
                    context.update(upd)
                    updates = context
            except Exception:
                continue
        return updates

    def after_model_op(self, context: dict[str, Any], output: Any) -> Any | None:
        out = output
        changed = False
        for p in self._plugins:
            try:
                maybe = p.after_model_op(context, out)
                if maybe is not None:
                    out = maybe
                    changed = True
            except Exception:
                continue
        return out if changed else None

    def spec_build_started(self, spec: Any) -> None:
        for p in self._plugins:
            with contextlib.suppress(Exception):
                p.spec_build_started(spec)

    def spec_build_completed(self, spec_dict: dict[str, Any]) -> dict[str, Any] | None:
        out = spec_dict
        changed = False
        for p in self._plugins:
            try:
                maybe = p.spec_build_completed(out)
                if isinstance(maybe, dict):
                    out = maybe
                    changed = True
            except Exception:
                continue
        return out if changed else None

    @staticmethod
    def _safe_call(fn: Callable, *args: Any, **kwargs: Any) -> Any:
        try:
            return fn(*args, **kwargs)
        except Exception:
            return None
