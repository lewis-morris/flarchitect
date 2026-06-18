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
                plugin = cls._coerce_optional(entry)
                if plugin is not None:
                    plugins.append(plugin)
        elif config_val:
            with contextlib.suppress(Exception):
                plugins.append(cls._coerce(config_val))
        return cls(plugins)

    @classmethod
    def _coerce_optional(cls, entry: Any) -> PluginBase | None:
        """Best-effort plugin coercion for list-based config values."""

        try:
            return cls._coerce(entry)
        except Exception:
            # Skip invalid plugins rather than breaking app startup.
            return None

    # Dispatch helpers
    def _for_each(self, func: Callable[[PluginBase], Any]) -> None:
        for plugin in self._plugins:
            self._safe_call(func, plugin)

    def _first_non_none(self, func: Callable[[PluginBase], Any]) -> Any:
        for p in self._plugins:
            result = self._safe_call(func, p)
            if result is not None:
                return result
        return None

    def _merge_context_updates(self, context: dict[str, Any], func: Callable[[PluginBase], Any]) -> dict[str, Any] | None:
        updated = False
        for plugin in self._plugins:
            result = self._safe_call(func, plugin)
            if isinstance(result, dict):
                context.update(result)
                updated = True
        return context if updated else None

    def _chain_first_arg(self, initial: Any, func: Callable[[PluginBase, Any], Any], *, require_dict: bool = False) -> Any | None:
        value = initial
        changed = False
        for plugin in self._plugins:
            result = self._safe_call(func, plugin, value)
            if result is None:
                continue
            if require_dict and not isinstance(result, dict):
                continue
            value = result
            changed = True
        return value if changed else None

    def request_started(self, request: Request) -> None:
        self._for_each(lambda p: p.request_started(request))

    def request_finished(self, request: Request, response: Response) -> Response | None:
        return self._first_non_none(lambda p: p.request_finished(request, response))

    def before_authenticate(self, context: dict[str, Any]) -> dict[str, Any] | None:
        return self._merge_context_updates(context, lambda p: p.before_authenticate(context))

    def after_authenticate(self, context: dict[str, Any], success: bool, user: Any | None) -> None:
        self._for_each(lambda p: p.after_authenticate(context, success, user))

    def before_model_op(self, context: dict[str, Any]) -> dict[str, Any] | None:
        return self._merge_context_updates(context, lambda p: p.before_model_op(context))

    def after_model_op(self, context: dict[str, Any], output: Any) -> Any | None:
        return self._chain_first_arg(output, lambda p, out: p.after_model_op(context, out))

    def spec_build_started(self, spec: Any) -> None:
        self._for_each(lambda p: p.spec_build_started(spec))

    def spec_build_completed(self, spec_dict: dict[str, Any]) -> dict[str, Any] | None:
        return self._chain_first_arg(spec_dict, lambda p, out: p.spec_build_completed(out), require_dict=True)

    @staticmethod
    def _safe_call(fn: Callable, *args: Any, **kwargs: Any) -> Any:
        try:
            return fn(*args, **kwargs)
        except Exception:
            return None
