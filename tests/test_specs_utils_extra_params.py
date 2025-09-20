"""Additional tests for ``flarchitect.specs.utils`` helpers."""

from __future__ import annotations

from typing import Callable

import pytest
from marshmallow import Schema
from werkzeug.routing import IntegerConverter, Map, UnicodeConverter

from flarchitect.specs.utils import (
    generate_delete_query_params,
    generate_get_query_params,
    get_param_schema,
    schema_name_resolver,
    scrape_extra_info_from_spec_data,
)


class WidgetModel:
    """Lightweight model stand-in for config lookups."""


class WidgetSchema(Schema):
    class Meta:
        model = WidgetModel


@pytest.fixture
def config_stub(monkeypatch: pytest.MonkeyPatch) -> Callable[[dict[str, object]], None]:
    """Patch ``get_config_or_model_meta`` with deterministic overrides."""

    def apply(overrides: dict[str, object]) -> None:
        def _lookup(key: str, *args, default=None, **_kwargs):
            effective_default = default
            if len(args) >= 4:
                effective_default = args[3]
            return overrides.get(key, effective_default)

        monkeypatch.setattr("flarchitect.specs.utils.get_config_or_model_meta", _lookup)

    return apply


def test_schema_name_resolver_respects_case_variants(config_stub: Callable[[dict[str, object]], None]) -> None:
    class FancyThingSchema(Schema):
        class Meta:
            model = WidgetModel

    config_stub({"API_SCHEMA_CASE": "camel"})
    assert schema_name_resolver(FancyThingSchema) == "fancyThing"

    config_stub({"API_SCHEMA_CASE": "snake"})
    assert schema_name_resolver(FancyThingSchema) == "fancy_thing"

    config_stub({"API_SCHEMA_CASE": "kebab"})
    assert schema_name_resolver(FancyThingSchema) == "fancy-thing"


def test_scrape_extra_info_handles_missing_keys(config_stub: Callable[[dict[str, object]], None], monkeypatch: pytest.MonkeyPatch) -> None:
    config_stub({"AUTO_NAME_ENDPOINTS": False})

    messages: list[tuple[int, str]] = []
    monkeypatch.setattr("flarchitect.specs.utils.logger.log", lambda level, msg: messages.append((level, msg)))

    def handler() -> None:
        """Handler docstring."""

    spec = {"input_schema": WidgetSchema, "function": handler}
    result = scrape_extra_info_from_spec_data(spec, method="GET", multiple=True)

    assert result["tag"] == "Unknown"
    assert result["summary"] is False
    assert result["description"] == "Handler docstring."
    assert any("Missing data" in msg for _level, msg in messages)


def test_scrape_extra_info_auto_names_summary(config_stub: Callable[[dict[str, object]], None]) -> None:
    config_stub({"AUTO_NAME_ENDPOINTS": True, "API_SCHEMA_CASE": "camel"})

    def handler() -> None:
        """Auto summary handler."""

    spec = {"model": WidgetModel, "output_schema": WidgetSchema, "function": handler, "multiple": True}
    result = scrape_extra_info_from_spec_data(spec, method="GET", multiple=True)

    assert result["summary"] == "Returns a list of `widgetModel`"
    assert result["description"] == "Auto summary handler."


def test_scrape_extra_info_config_overrides_summary_and_description(config_stub: Callable[[dict[str, object]], None]) -> None:
    config_stub({
        "AUTO_NAME_ENDPOINTS": True,
        "get_many_summary": "Configured summary",
        "get_many_description": "Configured description",
    })

    def handler() -> None:
        """Original docstring."""

    spec = {"model": WidgetModel, "output_schema": WidgetSchema, "function": handler, "multiple": True}
    result = scrape_extra_info_from_spec_data(spec, method="GET", multiple=True)

    assert result["summary"] == "Configured summary"
    assert result["description"] == "Configured description"


def test_get_param_schema_supports_core_converters() -> None:
    mapper = Map()
    assert get_param_schema(IntegerConverter(mapper)) == {"type": "integer"}
    assert get_param_schema(UnicodeConverter(mapper)) == {"type": "string"}
    class CustomConverter:
        pass
    assert get_param_schema(CustomConverter()) == {"type": "string"}


def test_generate_delete_query_params_respects_cascade_flag(config_stub: Callable[[dict[str, object]], None]) -> None:
    schema = WidgetSchema()

    config_stub({"API_ALLOW_CASCADE_DELETE": True})
    params = generate_delete_query_params(schema, WidgetModel)
    assert any(param["name"] == "cascade_delete" for param in params)

    config_stub({"API_ALLOW_CASCADE_DELETE": False})
    assert generate_delete_query_params(schema, WidgetModel) == []


def test_generate_get_query_params_include_deleted_and_pagination(config_stub: Callable[[dict[str, object]], None]) -> None:
    schema = WidgetSchema()

    config_stub({
        "API_SOFT_DELETE": True,
        "API_PAGINATION_SIZE_MAX": 250,
        "API_PAGINATION_SIZE_DEFAULT": 25,
    })
    params = generate_get_query_params(schema, WidgetModel)

    include_deleted = next(p for p in params if p["name"] == "include_deleted")
    assert include_deleted["schema"] == {"type": "boolean"}

    limit = next(p for p in params if p["name"] == "limit")
    assert limit["schema"]["example"] == 20
    assert "Default `25`" in limit["description"]
    assert "Maximum `250`" in limit["description"]

    page = next(p for p in params if p["name"] == "page")
    assert page["schema"]["example"] == 1

    config_stub({
        "API_SOFT_DELETE": False,
        "API_PAGINATION_SIZE_MAX": 50,
        "API_PAGINATION_SIZE_DEFAULT": 10,
    })
    params_no_soft = generate_get_query_params(schema, WidgetModel)
    assert all(p["name"] != "include_deleted" for p in params_no_soft)
    limit_no_soft = next(p for p in params_no_soft if p["name"] == "limit")
    assert "Default `10`" in limit_no_soft["description"]
    assert "Maximum `50`" in limit_no_soft["description"]
