"""Tests for create_response utility."""

from flask import Flask

from flarchitect.utils.response_helpers import create_response
from flarchitect.utils.responses import CustomResponse


def _make_app() -> Flask:
    app = Flask(__name__)
    app.config["API_VERSION"] = "1"
    return app


def test_create_response_processes_tuple_result() -> None:
    """Ensure tuple results are unpacked into the response."""
    app = _make_app()
    with app.test_request_context():
        resp = create_response(result=({"msg": "ok"}, 201))
        data = resp.get_json()
        assert data["value"] == {"msg": "ok"}
        assert data["status_code"] == 201
        assert resp.status_code == 201


def test_create_response_handles_dict_with_pagination() -> None:
    """Process dict results containing pagination fields."""
    app = _make_app()
    result = {"query": [1, 2], "next_url": "/next", "previous_url": "/prev"}
    with app.test_request_context():
        resp = create_response(result=result)
        data = resp.get_json()
        assert data["value"] == [1, 2]
        assert data["total_count"] == 2
        assert data["next_url"] == "/next"
        assert data["previous_url"] == "/prev"


def test_create_response_sets_errors_for_bad_status() -> None:
    """Errors are surfaced when status codes indicate failure."""
    app = _make_app()
    with app.test_request_context():
        resp = create_response(result=({"error": "bad"}, 400))
        data = resp.get_json()
        assert data["errors"] == {"error": "bad"}
        assert data["value"] is None
        assert data["status_code"] == 400
        assert resp.status_code == 400


def test_create_response_handles_custom_response() -> None:
    """CustomResponse instances expose pagination metadata."""
    app = _make_app()
    custom = CustomResponse(value={"msg": "ok"}, next_url="/next", previous_url="/prev", count=1)
    with app.test_request_context():
        resp = create_response(result=custom)
        data = resp.get_json()
        assert data["value"] == {"msg": "ok"}
        assert data["next_url"] == "/next"
        assert data["previous_url"] == "/prev"
        assert data["total_count"] == 1
