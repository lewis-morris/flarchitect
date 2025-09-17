from __future__ import annotations

from typing import Any

from flask import Request, Response

from demo.model_extension.model import create_app as create_app_models
from flarchitect.plugins import PluginBase


class TestPlugin(PluginBase):
    def __init__(self) -> None:
        self.request_started_count = 0
        self.request_finished_count = 0
        self.before_auth_calls = 0
        self.after_auth_calls = 0
        self.before_model_calls = 0
        self.after_model_calls = 0
        self.spec_started = False
        self.spec_completed = False

    def request_started(self, request: Request) -> None:
        self.request_started_count += 1

    def request_finished(self, request: Request, response: Response) -> Response | None:
        self.request_finished_count += 1
        return None

    def before_authenticate(self, context: dict[str, Any]) -> dict[str, Any] | None:
        self.before_auth_calls += 1
        return None

    def after_authenticate(self, context: dict[str, Any], success: bool, user: Any | None) -> None:
        self.after_auth_calls += 1

    def before_model_op(self, context: dict[str, Any]) -> dict[str, Any] | None:
        # Mutate POSTed book titles to include a marker
        self.before_model_calls += 1
        if context.get("method") == "POST" and getattr(context.get("model"), "__name__", "") == "Book":
            data = context.get("deserialized_data") or {}
            if isinstance(data, dict):
                new_data = dict(data)
                new_data["title"] = "[plugin] " + new_data.get("title", "")
                return {"deserialized_data": new_data}
        return None

    def after_model_op(self, context: dict[str, Any], output: Any) -> Any | None:
        self.after_model_calls += 1
        return None

    def spec_build_started(self, spec: Any) -> None:
        self.spec_started = True

    def spec_build_completed(self, spec_dict: dict[str, Any]) -> dict[str, Any] | None:
        self.spec_completed = True
        return None


def test_plugin_hooks_and_mutation():
    plugin = TestPlugin()
    app = create_app_models({"API_PLUGINS": [plugin]})
    client = app.test_client()

    # Trigger request hooks and a GET op
    resp = client.get("/api/books/1")
    assert resp.status_code == 200
    assert plugin.request_started_count >= 1
    assert plugin.request_finished_count >= 1

    # Prepare POST payload based on existing object
    data = resp.get_json()["value"]
    data.pop("id", None)
    # POST should have title mutated by plugin
    created = client.post("/api/books", json=data)
    assert created.status_code == 200
    title = created.get_json()["value"]["title"]
    assert title.startswith("[plugin] ")

    # Spec hooks fire when building OpenAPI document
    spec = client.get("/docs/apispec.json")
    assert spec.status_code == 200
    assert plugin.spec_started is True
    assert plugin.spec_completed is True
