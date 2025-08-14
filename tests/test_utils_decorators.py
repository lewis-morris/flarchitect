"""Tests for utility decorators."""

from __future__ import annotations

# Import modules directly to avoid executing ``flarchitect`` package-level code
import importlib.util
from collections import namedtuple
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from flask import Flask
from sqlalchemy.exc import ProgrammingError
from werkzeug.exceptions import NotFound

_BASE = Path(__file__).resolve().parents[1]


def _load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, _BASE / relative)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader  # for type checkers
    spec.loader.exec_module(module)
    return module


decorators = _load_module("decorators", "flarchitect/utils/decorators.py")
exceptions = _load_module("exceptions", "flarchitect/exceptions.py")

add_dict_to_query = decorators.add_dict_to_query
add_page_totals_and_urls = decorators.add_page_totals_and_urls
standardize_response = decorators.standardize_response
CustomHTTPException = exceptions.CustomHTTPException

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_app() -> Flask:
    """Create a Flask app for testing."""
    app = Flask(__name__)
    app.config["API_VERSION"] = "1"
    return app


# ---------------------------------------------------------------------------
# add_dict_to_query
# ---------------------------------------------------------------------------


def test_add_dict_to_query_converts_results() -> None:
    """Convert SQLAlchemy rows to dictionaries."""

    Row = namedtuple("Row", ["id", "name"])

    @add_dict_to_query
    def fetch() -> dict[str, Any]:
        return {"query": [Row(1, "a"), Row(2, "b")]}  # simulate row objects

    result = fetch()
    assert result["dictionary"] == [
        {"id": 1, "name": "a"},
        {"id": 2, "name": "b"},
    ]


def test_add_dict_to_query_ignores_non_asdict_objects() -> None:
    """Ignore objects lacking an ``_asdict`` method."""

    class Dummy:
        pass

    @add_dict_to_query
    def fetch() -> dict[str, Any]:
        return {"query": [Dummy(), Dummy()]}

    result = fetch()
    assert "dictionary" not in result


# ---------------------------------------------------------------------------
# add_page_totals_and_urls
# ---------------------------------------------------------------------------


def test_add_page_totals_and_urls_adds_metadata() -> None:
    """Attach pagination metadata and navigation URLs."""

    @add_page_totals_and_urls
    def fetch() -> dict[str, Any]:
        return {"query": [], "limit": 2, "page": 1, "total_count": 5}

    app = _make_app()
    with app.test_request_context("/items?page=1"):
        result = fetch()

    parsed = urlparse(result["next_url"])
    params = parse_qs(parsed.query)
    assert params["page"] == ["2"]
    assert params["limit"] == ["2"]
    assert result["previous_url"] is None
    assert result["current_page"] == 1
    assert result["total_pages"] == 3


def test_add_page_totals_and_urls_without_pagination() -> None:
    """Return ``None`` metadata when pagination fields missing."""

    @add_page_totals_and_urls
    def fetch() -> dict[str, Any]:
        return {"query": [], "limit": 2, "page": 1}

    app = _make_app()
    with app.test_request_context("/items"):
        result = fetch()

    assert result["next_url"] is None
    assert result["previous_url"] is None
    assert result["current_page"] is None
    assert result["total_pages"] is None


# ---------------------------------------------------------------------------
# standardize_response
# ---------------------------------------------------------------------------


def test_standardize_response_success() -> None:
    """Standard responses are wrapped correctly."""

    @standardize_response
    def view() -> dict[str, str]:
        return {"msg": "ok"}

    app = _make_app()
    with app.test_request_context("/"):
        resp = view()
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["value"] == {"msg": "ok"}
    assert "errors" not in data


def test_standardize_response_handles_http_exception() -> None:
    """Convert ``HTTPException`` instances to error responses."""

    @standardize_response
    def view() -> None:
        raise NotFound("missing")

    app = _make_app()
    with app.test_request_context("/"):
        resp = view()
    data = resp.get_json()
    assert resp.status_code == 404
    assert data["errors"] == {"error": "missing", "reason": "Not Found"}


def test_standardize_response_handles_programming_error() -> None:
    """Convert SQL ``ProgrammingError`` to a bad request response."""

    @standardize_response
    def view() -> None:
        raise ProgrammingError("SELECT", {}, Exception("syntax error"))

    app = _make_app()
    with app.test_request_context("/"):
        resp = view()
    data = resp.get_json()
    assert resp.status_code == 400
    assert data["errors"]["error"].startswith("SQL Format Error")
    assert data["errors"]["reason"] is None


def test_standardize_response_handles_custom_http_exception() -> None:
    """Handle ``CustomHTTPException`` via the error handler."""

    @standardize_response
    def view() -> None:
        raise CustomHTTPException(418, "No tea")

    app = _make_app()
    with app.test_request_context("/"):
        resp = view()
    data = resp.get_json()
    assert resp.status_code == 418
    assert data["errors"] == {"error": "No tea", "reason": "I'm a Teapot"}
    assert data["value"] is None
