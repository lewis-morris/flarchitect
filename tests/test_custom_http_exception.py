"""Tests for CustomHTTPException and related helpers."""

from flask import Flask

from flarchitect.exceptions import CustomHTTPException, _handle_exception


def test_custom_http_exception_to_dict() -> None:
    exc = CustomHTTPException(400, "Invalid input")
    assert exc.to_dict() == {
        "status_code": 400,
        "status_text": "Bad Request",
        "reason": "Invalid input",
    }


def test_handle_exception_returns_response() -> None:
    app = Flask(__name__)
    with app.test_request_context():
        response = _handle_exception("Unexpected", 500, error_name="Server Error", print_exc=False)
        data = response.get_json()
        assert response.status_code == 500
        assert data["errors"] == {"error": "Unexpected", "reason": "Server Error"}
        assert data["status_code"] == 500
