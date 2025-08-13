import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

import pytz
from flask import Response, current_app, g, jsonify

from flarchitect.utils.config_helpers import get_config_or_model_meta, is_xml
from flarchitect.utils.core_utils import convert_case, dict_to_xml
from flarchitect.utils.response_filters import _filter_response_data


def create_response(
    value: Any | None = None,
    status: int = 200,
    errors: str | list | None = None,
    count: int | None = 1,
    next_url: str | None = None,
    previous_url: str | None = None,
    response_ms: float | None = None,
) -> Response:
    """Create a standardized Flask :class:`~flask.Response`.

    Args:
        value (Optional[Any]): The value to be returned.
        status (int): HTTP status code.
        errors (Optional[Union[str, List]]): Error messages.
        count (Optional[int]): Number of objects returned.
        next_url (Optional[str]): URL for the next page of results.
        previous_url (Optional[str]): URL for the previous page of results.
        response_ms (Optional[float]): The time taken to generate the response.

    Notes:
        If the application configuration defines ``API_FINAL_CALLBACK`` it will
        be invoked with the assembled response payload prior to serialization.
        This allows custom mutation of the outgoing data, such as injecting
        additional metadata.

    Returns:
        Response: A standardized response object.
    """
    if isinstance(value, tuple) and len(value) == 2 and isinstance(value[1], int):
        status, value = value[1], value[0]

    if response_ms is None:
        # error responses were missing this. Added here to ensure it's always present.
        response_ms = round((time.time() - g.start_time) * 1000, 0) if g.get("start_time") else "n/a"

    current_time_with_tz = datetime.now(pytz.utc).isoformat()
    data = {
        "api_version": current_app.config.get("API_VERSION"),
        "datetime": current_time_with_tz,
        "value": value.value if hasattr(value, "value") else value,
        "status_code": status,
        "errors": errors[0] if errors and isinstance(errors, list) else errors,
        "response_ms": response_ms,
        "total_count": count,
        "next_url": next_url,
        "previous_url": previous_url,
    }

    data = _filter_response_data(data)
    data = {convert_case(k, get_config_or_model_meta("API_FIELD_CASE", default="snake_case")): v for k, v in data.items()}

    # Optional hook allowing applications to post-process the outgoing payload.
    # ``API_FINAL_CALLBACK`` should be a callable that accepts the response
    # dictionary and returns the modified dictionary. This can be used to inject
    # custom metadata or otherwise mutate the payload before serialization.
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
