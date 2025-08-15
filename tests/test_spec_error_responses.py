from flask import Flask

from flarchitect.specs.utils import build_error_response, initialize_spec_template


def _make_app() -> Flask:
    app = Flask(__name__)
    app.config["API_VERSION"] = "1"
    app.config["API_AUTHENTICATE"] = True
    return app


def test_build_error_response_includes_example_and_links() -> None:
    app = _make_app()
    with app.test_request_context():
        resp = build_error_response(404, {"about": {"operationId": "getWidget"}})
        example = resp["content"]["application/json"]["example"]
        assert resp["description"].lower() == "not found"
        assert example["status_code"] == 404
        assert example["errors"] == {"error": "Not Found"}
        assert resp["links"]["about"]["operationId"] == "getWidget"


def test_initialize_spec_template_passes_configured_links() -> None:
    app = _make_app()
    app.config["API_LINKS"] = {
        "404": {"about": {"operationId": "getWidget"}},
        "401": {"login": {"operationId": "login"}},
    }
    with app.test_request_context():
        spec = initialize_spec_template("GET", error_responses=[404, 401])
        resp_404 = spec["responses"]["404"]
        resp_401 = spec["responses"]["401"]
        assert resp_404["links"]["about"]["operationId"] == "getWidget"
        assert resp_401["links"]["login"]["operationId"] == "login"
        assert resp_404["content"]["application/json"]["example"]["status_code"] == 404
        assert resp_401["content"]["application/json"]["example"]["status_code"] == 401
