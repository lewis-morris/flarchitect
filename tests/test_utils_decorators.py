# isort: skip_file
"""Tests for utility decorators."""

from __future__ import annotations

import sys
import types
from collections import namedtuple
from pathlib import Path
from typing import Any

from flask import Flask
from werkzeug.exceptions import NotFound

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "flarchitect"
stub = types.ModuleType("flarchitect")
stub.__path__ = [str(PACKAGE_ROOT)]
sys.modules.setdefault("flarchitect", stub)

# Minimal stubs for ``flarchitect.schemas`` to avoid heavy dependencies.
schemas_stub = types.ModuleType("flarchitect.schemas")
utils_stub = types.ModuleType("flarchitect.schemas.utils")
utils_stub.deserialize_data = lambda *_, **__: {}  # type: ignore[assignment]
utils_stub.dump_schema_if_exists = lambda *_, **__: {}  # type: ignore[assignment]
bases_stub = types.ModuleType("flarchitect.schemas.bases")


class AutoSchema:  # pragma: no cover - simple stub
    pass


bases_stub.AutoSchema = AutoSchema
schemas_stub.utils = utils_stub
schemas_stub.bases = bases_stub
sys.modules["flarchitect.schemas"] = schemas_stub
sys.modules["flarchitect.schemas.utils"] = utils_stub
sys.modules["flarchitect.schemas.bases"] = bases_stub

from flarchitect.exceptions import CustomHTTPException  # noqa: E402
from flarchitect.utils.decorators import add_dict_to_query  # noqa: E402
from flarchitect.utils.decorators import add_page_totals_and_urls  # noqa: E402
from flarchitect.utils.decorators import standardize_response  # noqa: E402


def _make_app() -> Flask:
    """Create a Flask app for testing."""
    app = Flask(__name__)
    app.config["API_VERSION"] = "1"
    return app


# ---------------------------------------------------------------------------
# add_dict_to_query
# ---------------------------------------------------------------------------

Row = namedtuple("Row", ["id", "name"])


@add_dict_to_query
def _list_query() -> dict[str, Any]:
    """Return a list of mock SQLAlchemy rows."""
    return {"query": [Row(1, "a"), Row(2, "b")]}


@add_dict_to_query
def _single_query() -> dict[str, Any]:
    """Return a single mock SQLAlchemy row."""
    return {"query": Row(1, "a")}


@add_dict_to_query
def _invalid_query() -> dict[str, Any]:
    """Return objects lacking ``_asdict`` to trigger failure branch."""
    return {"query": [object(), object()]}


def test_add_dict_to_query_transforms_results() -> None:
    """Rows are converted to dictionaries for both single and list outputs."""
    assert _list_query()["dictionary"] == [
        {"id": 1, "name": "a"},
        {"id": 2, "name": "b"},
    ]
    assert _single_query()["dictionary"] == {"id": 1, "name": "a"}


def test_add_dict_to_query_ignores_unmappable_objects() -> None:
    """Objects without ``_asdict`` do not add a dictionary key."""
    result = _invalid_query()
    assert "dictionary" not in result


# ---------------------------------------------------------------------------
# add_page_totals_and_urls
# ---------------------------------------------------------------------------


@add_page_totals_and_urls
def _paginated() -> dict[str, Any]:
    """Return paginated data with required metadata."""
    return {"query": [], "limit": 10, "page": 2, "total_count": 35}


@add_page_totals_and_urls
def _no_pagination() -> dict[str, Any]:
    """Return data missing pagination info to trigger failure branch."""
    return {"query": [], "limit": 10, "page": 1, "total_count": 0}


def test_add_page_totals_and_urls_generates_metadata() -> None:
    """Pagination metadata and URLs are correctly generated."""
    app = _make_app()
    with app.test_request_context("/items?page=2"):
        result = _paginated()
        assert result["current_page"] == 2
        assert result["total_pages"] == 4
        assert "page=3" in result["next_url"] and "limit=10" in result["next_url"]
        assert (
            "page=1" in result["previous_url"] and "limit=10" in result["previous_url"]
        )


def test_add_page_totals_and_urls_handles_missing_metadata() -> None:
    """When totals are missing, pagination fields are ``None``."""
    app = _make_app()
    with app.test_request_context("/items?page=1"):
        result = _no_pagination()
        assert result["next_url"] is None
        assert result["previous_url"] is None
        assert result["current_page"] is None
        assert result["total_pages"] is None


# ---------------------------------------------------------------------------
# standardize_response
# ---------------------------------------------------------------------------


def test_standardize_response_handles_http_exception() -> None:
    """HTTPException results in a structured error response."""
    app = _make_app()

    @standardize_response
    def route() -> None:
        raise NotFound(description="missing")

    with app.test_request_context("/items"):
        resp = route()
        data = resp.get_json()
        assert resp.status_code == 404
        assert data["errors"] == {"error": "missing", "reason": "Not Found"}


def test_standardize_response_handles_programming_error(monkeypatch) -> None:
    """SQLAlchemy ``ProgrammingError`` is standardised to a 400 response."""
    app = _make_app()

    class DummyProgrammingError(Exception):
        def __str__(self) -> str:  # pragma: no cover - trivial
            return "(psycopg2.ProgrammingError) syntax error"

    monkeypatch.setattr(
        "flarchitect.utils.decorators.ProgrammingError", DummyProgrammingError
    )

    @standardize_response
    def route() -> None:
        raise DummyProgrammingError()

    with app.test_request_context("/items"):
        resp = route()
        data = resp.get_json()
        assert resp.status_code == 400
        assert data["errors"] == {
            "error": "SQL Format Error: Syntax error",
            "reason": None,
        }


def test_standardize_response_handles_custom_http_exception() -> None:
    """``CustomHTTPException`` is converted to its defined status and error."""
    app = _make_app()

    @standardize_response
    def route() -> None:
        raise CustomHTTPException(418, "nope")

    with app.test_request_context("/items"):
        resp = route()
        data = resp.get_json()
        assert resp.status_code == 418
        assert data["errors"] == {"error": "nope", "reason": "I'm a Teapot"}
