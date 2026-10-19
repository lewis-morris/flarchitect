"""Preserve response naming, filtering and callbacks while reducing lookups."""

from xml.etree import ElementTree

import pytest
from flask import Flask

from flarchitect.utils import response_helpers


@pytest.mark.parametrize("accept", ["application/json", "application/xml"])
@pytest.mark.parametrize(
    ("style", "status_key", "total_key"),
    [
        ("camel", "statusCode", "totalCount"),
        ("pascal", "StatusCode", "TotalCount"),
        ("snake", "status_code", "total_count"),
        ("screaming_snake", "STATUS_CODE", "TOTAL_COUNT"),
        ("kebab", "status-code", "total-count"),
        ("screaming_kebab", "STATUS-CODE", "TOTAL-COUNT"),
        ("unknown", "status_code", "total_count"),
        (None, "status_code", "total_count"),
    ],
)
def test_response_case_and_content_negotiation(style, status_key, total_key, accept):
    app = Flask(__name__)
    if style is not None:
        app.config["API_FIELD_CASE"] = style
    with app.test_request_context(headers={"Accept": accept}):
        response = response_helpers.create_response(value="hello", status=201, count=7, response_ms=4)
        if accept == "application/json":
            payload = response.get_json()
            assert payload[status_key] == 201
            assert payload[total_key] == 7
            assert response.status_code == 201
        else:
            payload = ElementTree.fromstring(response.get_data(as_text=True))
            assert payload.find(status_key).text == "201"
            assert payload.find(total_key).text == "7"
            # XML must carry the same transport status as its envelope.
            assert response.status_code == 201
        assert response.mimetype == accept


@pytest.mark.parametrize("accept", ["application/json", "application/xml"])
def test_callback_receives_filtered_converted_errors(accept):
    app = Flask(__name__)
    seen = []

    def callback(payload):
        seen.append(dict(payload))
        payload["callback_marker"] = "kept"
        return payload

    app.config.update(
        API_FIELD_CASE="camel",
        API_DUMP_DATETIME=False,
        API_DUMP_VERSION=False,
        API_DUMP_RESPONSE_MS=False,
        API_DUMP_NULL_NEXT_URL=False,
        API_DUMP_NULL_PREVIOUS_URL=False,
        API_FINAL_CALLBACK=callback,
    )
    with app.test_request_context(headers={"Accept": accept}):
        response = response_helpers.create_response(result=({"reason": "bad"}, 400), response_ms=4)
        assert seen == [{"value": None, "statusCode": 400, "errors": {"reason": "bad"}, "totalCount": 1}]
        if accept == "application/json":
            assert response.get_json() == {**seen[0], "callback_marker": "kept"}
            assert response.status_code == 400
        else:
            payload = ElementTree.fromstring(response.get_data(as_text=True))
            assert payload.find("errors/reason").text == "bad"
            assert payload.find("callback_marker").text == "kept"
            assert response.status_code == 400


def test_response_case_is_resolved_once_per_response_and_not_shared_between_requests(monkeypatch):
    app = Flask(__name__)
    original = response_helpers.get_config_or_model_meta
    calls = []

    def lookup(key, *args, **kwargs):
        if key == "API_FIELD_CASE":
            calls.append(key)
        return original(key, *args, **kwargs)

    monkeypatch.setattr(response_helpers, "get_config_or_model_meta", lookup)
    for style, expected_key in [("camel", "statusCode"), ("kebab", "status-code"), ("snake", "status_code")]:
        app.config["API_FIELD_CASE"] = style
        with app.test_request_context():
            payload = response_helpers.create_response(value="hello", response_ms=4).get_json()
            assert expected_key in payload
            assert "errors" not in payload
    assert calls == ["API_FIELD_CASE"] * 3
