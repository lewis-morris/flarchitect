"""Utilities for assembling documentation bundles that combine auto and manual routes."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from flask import Flask

EXCLUDED_METHODS = {"HEAD", "OPTIONS"}


def build_docs_bundle(
    *,
    app: Flask,
    route_spec: list[dict[str, Any]] | None,
    created_routes: dict[str, dict[str, Any]] | None,
) -> dict[str, Any]:
    """Produce a merged view of generated and custom routes."""

    route_spec = route_spec or []
    created_routes = created_routes or {}

    spec_by_func = {route.get("function"): route for route in route_spec if route.get("function")}
    auto_keys = {
        (info["method"].upper(), info["url"]): info
        for info in created_routes.values()
        if info.get("method") and info.get("url")
    }

    routes: list[dict[str, Any]] = []
    conflicts: defaultdict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    recorded_keys: set[tuple[str, str]] = set()

    for rule in app.url_map.iter_rules():
        methods = sorted(m for m in rule.methods if m not in EXCLUDED_METHODS)
        if not methods:
            continue

        endpoint = rule.endpoint
        func = app.view_functions.get(endpoint)
        if func is None:
            continue

        blueprint, _, endpoint_name = endpoint.partition(".")
        blueprint = blueprint or None

        spec = spec_by_func.get(func)
        is_managed = bool(getattr(func, "_has_schema_constructor", False))

        for method in methods:
            auto_meta = auto_keys.get((method, rule.rule))
            route_entry = {
                "url": rule.rule,
                "method": method,
                "endpoint": endpoint_name,
                "blueprint": blueprint,
                "managed": is_managed,
                "auto_generated": bool(auto_meta),
                "model": _model_name(auto_meta or spec),
                "input_schema": _schema_name((spec or {}).get("input_schema")),
                "output_schema": _schema_name((spec or {}).get("output_schema")),
                "exists": True,
            }
            routes.append(route_entry)
            conflicts[(method, rule.rule)].append(route_entry)
            recorded_keys.add((method, rule.rule))

    for (method, url), meta in auto_keys.items():
        if (method, url) in recorded_keys:
            continue
        missing_entry = {
            "url": url,
            "method": method,
            "endpoint": meta.get("name"),
            "blueprint": "api",
            "managed": True,
            "auto_generated": True,
            "model": _model_name(meta),
            "input_schema": _schema_name(meta.get("input_schema")),
            "output_schema": _schema_name(meta.get("output_schema")),
            "exists": False,
        }
        routes.append(missing_entry)
        conflicts[(method, url)].append(missing_entry)

    conflict_list = [
        {
            "method": method,
            "url": url,
            "routes": entries,
        }
        for (method, url), entries in conflicts.items()
        if len(entries) > 1
    ]

    return {
        "routes": sorted(routes, key=lambda item: (item["url"], item["method"])),
        "conflicts": sorted(conflict_list, key=lambda item: (item["url"], item["method"])),
    }


def _schema_name(schema: Any) -> str | None:
    if schema is None:
        return None
    if hasattr(schema, "__name__"):
        return schema.__name__
    return schema.__class__.__name__


def _model_name(info: dict[str, Any] | None) -> str | None:
    if not info:
        return None
    model = info.get("model")
    if model is None:
        return None
    if hasattr(model, "__name__"):
        return model.__name__
    return str(model)


__all__ = ["build_docs_bundle"]
