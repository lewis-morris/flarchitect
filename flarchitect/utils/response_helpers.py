import time
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from flask import Response, current_app, g, jsonify

from flarchitect.utils.config_helpers import get_config_or_model_meta, is_xml
from flarchitect.utils.core_utils import convert_case, dict_to_xml
from flarchitect.utils.general import HTTP_BAD_REQUEST, handle_result
from flarchitect.utils.response_filters import _filter_response_data


def _prepare_response_components(
    value: Any | None,
    status: int,
    errors: str | list | dict | None,
    count: int | None,
    next_url: str | None,
    previous_url: str | None,
    result: Any | None,
) -> tuple[int, Any | None, str | list | dict | None, int | None, str | None, str | None]:
    """Normalise response components before serialisation.

    ``create_response`` accepts values both via the ``value`` parameter and
    through the richer ``result`` argument. The latter is preferred and may be a
    tuple, mapping or ``CustomResponse``-style container. This helper distils
    those variants into consistent primitives which keeps the main function
    focused on building the envelope.
    """

    if result is not None:
        status, value, count, next_url, previous_url = handle_result(result)
        errors = None if status < HTTP_BAD_REQUEST else value
        if errors:
            value = None
    elif isinstance(value, tuple) and len(value) == 2 and isinstance(value[1], int):
        status, value = value[1], value[0]

    return status, value, errors, count, next_url, previous_url


def _ensure_response_ms(response_ms: float | None) -> float | str:
    """Return a response-time metric, falling back to ``g.start_time``.

    When ``create_response`` is called in error handlers there may be no
    explicit ``response_ms`` value supplied. We default to calculating it from
    the Flask ``g`` object where the project records the request start time. If
    even that is unavailable we emit ``"n/a"`` so the schema remains stable.
    """

    if response_ms is not None:
        return response_ms

    start_time = g.get("start_time") if hasattr(g, "get") else None
    if start_time:
        return round((time.time() - start_time) * 1000, 0)

    return "n/a"


def _extract_serialisable_value(value: Any | None) -> Any | None:
    """Unwrap container types that expose a ``value`` attribute."""

    return getattr(value, "value", value)


def create_response(
    value: Any | None = None,
    status: int = 200,
    errors: str | list | dict | None = None,
    count: int | None = 1,
    next_url: str | None = None,
    previous_url: str | None = None,
    response_ms: float | None = None,
    result: Any | None = None,
) -> Response:
    """Create a standardised Flask :class:`~flask.Response`.

    Args:
        value (Optional[Any]): The value to be returned.
        status (int): HTTP status code.
        errors (Optional[Union[str, List, Dict]]): Error messages.
        count (Optional[int]): Number of objects returned.
        next_url (Optional[str]): URL for the next page of results.
        previous_url (Optional[str]): URL for the previous page of results.
        response_ms (Optional[float]): The time taken to generate the response.
        result (Optional[Any]): Raw result to be processed into a response. When
            provided, other parameters are ignored.

    Notes:
        If the application configuration defines ``API_FINAL_CALLBACK`` it will
        be invoked with the assembled response payload prior to serialisation.
        This allows custom mutation of the outgoing data, such as injecting
        additional metadata.

    Returns:
        Response: A standardised response object.
    """
    status, value, errors, count, next_url, previous_url = _prepare_response_components(
        value,
        status,
        errors,
        count,
        next_url,
        previous_url,
        result,
    )

    response_ms = _ensure_response_ms(response_ms)

    current_time_with_tz = datetime.now(timezone.utc).isoformat()
    # Best-effort request id from Flask context (set by Architect.before_request)
    try:
        request_id = getattr(g, "request_id", None)
    except Exception:
        request_id = None
    data = {
        "api_version": current_app.config.get("API_VERSION"),
        "datetime": current_time_with_tz,
        "value": _extract_serialisable_value(value),
        "status_code": status,
        "errors": errors[0] if errors and isinstance(errors, list) else errors,
        "response_ms": response_ms,
        "total_count": count,
        "next_url": next_url,
        "previous_url": previous_url,
    }
    # Only add when available; filtering controls visibility by config
    if request_id:
        data["request_id"] = request_id

    data = _filter_response_data(data)
    # Default to 'snake' to match supported case values
    data = {convert_case(k, get_config_or_model_meta("API_FIELD_CASE", default="snake")): v for k, v in data.items()}

    # Optional hook allowing applications to post-process the outgoing payload.
    # ``API_FINAL_CALLBACK`` should be a callable that accepts the response
    # dictionary and returns the modified dictionary. This can be used to inject
    # custom metadata or otherwise mutate the payload before serialisation.
    final_callback: Callable[[dict[str, Any]], dict[str, Any]] | None = get_config_or_model_meta("API_FINAL_CALLBACK")
    if final_callback:
        data = final_callback(data)

    if is_xml():
        type_ = "text/xml" if get_config_or_model_meta("API_XML_AS_TEXT", default=False) else "application/xml"
        response = Response(dict_to_xml(data), mimetype=type_)
    else:
        response = jsonify(data)
        response.status_code = status

    return response
