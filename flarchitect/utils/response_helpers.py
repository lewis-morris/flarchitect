import time
from datetime import datetime
from typing import Any

import pytz
from flask import Response, current_app, g, jsonify

from flarchitect.utils.config_helpers import get_config_or_model_meta, is_xml
from flarchitect.utils.core_utils import convert_case, dict_to_xml, get_count
from flarchitect.utils.general import HTTP_BAD_REQUEST, HTTP_OK
from flarchitect.utils.response_filters import _filter_response_data


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
    """
    Create a standardized response.

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

    Returns:
        Response: A standardized response object.
    """
    if result is not None:
        from flarchitect.utils.responses import CustomResponse

        status, value, count, next_url, previous_url = HTTP_OK, result, 1, None, None
        if isinstance(result, tuple):
            status, value = (result[1], result[0]) if len(result) == 2 and isinstance(result[1], int) else (HTTP_OK, result)
        if isinstance(value, dict):
            value_dict = value
            value, count = value_dict.get("query", value_dict), get_count(value_dict, value_dict.get("query"))
            next_url, previous_url = value_dict.get("next_url"), value_dict.get("previous_url")
        elif isinstance(value, CustomResponse):
            next_url, previous_url, count = value.next_url, value.previous_url, value.count
        errors = None if status < HTTP_BAD_REQUEST else value
        if errors:
            value = None
    elif isinstance(value, tuple) and len(value) == 2 and isinstance(value[1], int):
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

    final_hook = get_config_or_model_meta("API_FINAL_CALLBACK")
    if final_hook:
        data = final_hook(data)

    if is_xml():
        type_ = "text/xml" if get_config_or_model_meta("API_XML_AS_TEXT", default=False) else "application/xml"
        response = Response(dict_to_xml(data), mimetype=type_)
    else:
        response = jsonify(data)
        response.status_code = status

    return response
