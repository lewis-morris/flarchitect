"""Server-Sent Events (SSE) helpers with schema-aware payload support."""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any, Callable

from flask import Response, current_app, stream_with_context


def sse_message(
    data: Any,
    *,
    event: str | None = None,
    id: str | None = None,
    retry: int | None = None,
    encoder: Callable[[Any], str] | None = None,
) -> str:
    """Serialise ``data`` into a compliant SSE message string."""

    encode = encoder or (lambda value: json.dumps(value, default=_json_default))
    payload = encode(data)
    if not isinstance(payload, str):  # pragma: no cover - defensive
        payload = str(payload)

    lines: list[str] = []
    if event:
        lines.append(f"event: {event}")
    if id:
        lines.append(f"id: {id}")
    if retry is not None:
        lines.append(f"retry: {int(retry)}")

    for chunk in payload.splitlines() or [""]:
        lines.append(f"data: {chunk}")

    lines.append("")  # message terminator
    return "\n".join(lines)


def model_event(
    instance: Any,
    *,
    schema: Any | None = None,
    event: str | None = None,
    id: str | None = None,
    retry: int | None = None,
) -> str:
    """Render an SSE message for a model instance using an optional schema."""

    if schema is not None:
        from flarchitect.schemas.utils import dump_schema_if_exists

        serialized = dump_schema_if_exists(schema, instance, isinstance(instance, list))
    else:
        serialized = instance
    return sse_message(serialized, event=event, id=id, retry=retry)


def stream_sse_response(messages: Iterable[str]) -> Response:
    """Return a streaming Flask ``Response`` that yields prebuilt SSE messages."""

    def _event_stream():
        for message in messages:
            yield f"{message}\n"

    return current_app.response_class(stream_with_context(_event_stream()), mimetype="text/event-stream")


def stream_model_events(
    instances: Iterable[Any],
    *,
    schema: Any | None = None,
    event: str | None = None,
    id_factory: Callable[[Any, int], str | None] | None = None,
    retry: int | None = None,
) -> Response:
    """Stream model instances as SSE messages using an optional schema."""

    def _messages():
        for index, obj in enumerate(instances):
            event_id = id_factory(obj, index) if id_factory else None
            yield model_event(obj, schema=schema, event=event, id=event_id, retry=retry)

    return stream_sse_response(_messages())


def _json_default(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:  # pragma: no cover - defensive
            return str(value)
    if hasattr(value, "__dict__"):
        return value.__dict__
    return str(value)


__all__ = [
    "sse_message",
    "model_event",
    "stream_sse_response",
    "stream_model_events",
]
