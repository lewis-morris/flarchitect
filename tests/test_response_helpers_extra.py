from flask import Flask, g

from flarchitect.utils.response_helpers import create_response


def test_create_response_final_callback_and_request_context():
    app = Flask(__name__)
    app.config["API_VERSION"] = "X"
    app.config["API_DUMP_REQUEST_ID"] = True

    called = {}

    def final_cb(d: dict):
        called["ok"] = True
        d["extra"] = 1
        return d

    app.config["API_FINAL_CALLBACK"] = final_cb

    with app.app_context():
        with app.test_request_context("/"):
            # seed timing + request id in g
            g.start_time = 0.0
            g.request_id = "rid-1"
            resp = create_response(result={"query": {"a": 1}})
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["api_version"] == "X"
            assert data["request_id"] == "rid-1"
            assert data.get("extra") == 1
            assert called.get("ok") is True


def test_create_response_xml_serialization():
    app = Flask(__name__)
    app.config["API_VERSION"] = "1"
    app.config["API_XML_AS_TEXT"] = True
    with app.app_context():
        # trigger XML via Accept header
        with app.test_request_context("/", headers={"Accept": "application/xml"}):
            resp = create_response(result={"query": [{"a": 1}, {"a": 2}]})
            # text/xml when API_XML_AS_TEXT True
            assert resp.mimetype == "text/xml"
            body = resp.get_data(as_text=True)
            assert "<root>" in body


def test_create_response_response_ms_numeric():
    import time

    app = Flask(__name__)
    with app.app_context():
        with app.test_request_context("/"):
            g.start_time = time.time() - 0.001
            resp = create_response(result={"query": {"a": 1}})
            data = resp.get_json()
            assert isinstance(data.get("response_ms"), (int, float))
