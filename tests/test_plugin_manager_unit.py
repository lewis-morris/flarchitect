from __future__ import annotations

from typing import Any, Callable

import pytest
from flask import Response

from flarchitect.plugins import PluginBase, PluginManager


class _GoodPlugin(PluginBase):
    def __init__(self) -> None:
        self.ctx_updates = 0
        self.after_outs: list[Any] = []

    def before_authenticate(self, context: dict[str, Any]) -> dict[str, Any] | None:
        self.ctx_updates += 1
        return {"marker": self.ctx_updates}

    def before_model_op(self, context: dict[str, Any]) -> dict[str, Any] | None:
        return {"model_marker": True}

    def after_model_op(self, context: dict[str, Any], output: Any) -> Any | None:
        # Transform output by wrapping in a dict
        wrapped = {"wrapped": output}
        self.after_outs.append(wrapped)
        return wrapped

    def request_finished(self, request, response: Response) -> Response | None:  # type: ignore[override]
        # Return a response object to test _first_non_none
        return Response("ok", status=201)

    def spec_build_completed(self, spec_dict: dict[str, Any]) -> dict[str, Any] | None:
        # mutate spec
        new = dict(spec_dict)
        new["x"] = 1
        return new


class _NoopPlugin(PluginBase):
    pass


class _RaisingPlugin(PluginBase):
    def request_started(self, request) -> None:  # type: ignore[override]
        raise RuntimeError("boom")

    def request_finished(self, request, response):  # type: ignore[override]
        raise RuntimeError("boom")

    def before_authenticate(self, context: dict[str, Any]) -> dict[str, Any] | None:
        raise RuntimeError("boom")

    def after_model_op(self, context: dict[str, Any], output: Any) -> Any | None:
        raise RuntimeError("boom")

    def spec_build_completed(self, spec_dict: dict[str, Any]) -> dict[str, Any] | None:
        raise RuntimeError("boom")


def _factory() -> PluginBase:
    return _GoodPlugin()


def test_coercion_and_from_config() -> None:
    # Instance, class, and factory are accepted; invalids are ignored
    mgr = PluginManager.from_config([
        _GoodPlugin(),
        _GoodPlugin,  # class
        _factory,  # callable factory
        object(),  # ignored
    ])
    # Should coerce to 3 plugins
    assert isinstance(mgr, PluginManager)


def test_request_and_finish_dispatch() -> None:
    good = _GoodPlugin()
    mgr = PluginManager([_NoopPlugin(), _RaisingPlugin(), good])

    # request_started should ignore errors
    mgr.request_started(object())

    # request_finished returns first non-None result, swallowing errors
    resp = mgr.request_finished(object(), Response("body"))
    assert isinstance(resp, Response)
    assert resp.status_code == 201


def test_before_after_hooks_and_spec_mutation() -> None:
    good = _GoodPlugin()
    mgr = PluginManager([_RaisingPlugin(), _NoopPlugin(), good])

    ctx: dict[str, Any] = {"user": 1}
    updated = mgr.before_authenticate(ctx)
    # Updates merged into the original context
    assert updated is ctx and ctx["marker"] == 1

    # before_model_op applies its own updates
    updated2 = mgr.before_model_op(ctx)
    assert updated2 is ctx and ctx["model_marker"] is True

    # after_model_op returns transformed output (not None) when changed
    out = mgr.after_model_op(ctx, {"a": 1})
    assert out == {"wrapped": {"a": 1}}

    # spec_build_completed aggregates dict results and returns the last
    spec: dict[str, Any] = {"openapi": "3.1.0"}
    changed = mgr.spec_build_completed(spec)
    assert isinstance(changed, dict) and changed.get("x") == 1


def test_safe_call_exception_is_none() -> None:
    def boom() -> None:
        raise RuntimeError

    assert PluginManager._safe_call(boom) is None
