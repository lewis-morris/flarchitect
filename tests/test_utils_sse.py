"""Tests for SSE helpers."""

from __future__ import annotations

from dataclasses import dataclass

from flask import Flask

from flarchitect.utils.sse import model_event, sse_message, stream_model_events, stream_sse_response


def test_sse_message_formats_fields():
    message = sse_message({"hello": "world"}, event="update", id="42", retry=1000)
    assert "event: update" in message
    assert "id: 42" in message
    assert "retry: 1000" in message
    assert "data: {\"hello\": \"world\"}" in message
    assert message.endswith("\n")


@dataclass
class Dummy:
    id: int
    name: str


def test_model_event_serialises_with_schema():
    class DummySchema:
        def dump(self, obj, many=None):  # pragma: no cover - illustrative
            return {"identifier": obj.id, "label": obj.name}

    message = model_event(Dummy(1, "alpha"), schema=DummySchema(), event="dummy")
    assert "event: dummy" in message
    assert "identifier" in message


def test_stream_helpers_produce_response():
    app = Flask(__name__)

    with app.test_request_context("/"):
        response = stream_sse_response(["event: ping\ndata: 1\n\n"])
        body = b"".join(
            chunk.encode() if isinstance(chunk, str) else chunk for chunk in response.response
        )
        assert b"event: ping" in body

        response2 = stream_model_events([Dummy(1, "alpha"), Dummy(2, "beta")])
        payload = b"".join(
            chunk.encode() if isinstance(chunk, str) else chunk for chunk in response2.response
        )
        assert payload.count(b"data:") >= 2
