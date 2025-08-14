"""Tests for CustomHTTPException and related helpers."""

from flask import Flask

from flarchitect.exceptions import CustomHTTPException, _handle_exception, handle_http_exception


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


def test_handle_http_exception_returns_json() -> None:
    app = Flask(__name__)
    app.register_error_handler(CustomHTTPException, handle_http_exception)

    @app.get("/api/error")
    def error_route() -> dict[str, str]:  # pragma: no cover - simple route for test
        raise CustomHTTPException(401, "Auth required")

    with app.test_client() as client:
        response = client.get("/api/error")
        data = response.get_json()
        assert response.status_code == 401
        assert data["errors"] == {"error": "Unauthorized", "reason": "Auth required"}
