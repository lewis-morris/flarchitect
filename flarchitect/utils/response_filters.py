from typing import Any

from flarchitect.utils.config_helpers import get_config_or_model_meta


def _filter_response_data(data: dict[str, Any]) -> dict[str, Any]:
    """
    Filter response data based on configuration settings.

    Args:
        data (Dict[str, Any]): The response data to be filtered.

    Returns:
        Dict[str, Any]: The filtered response data.
    """
    filters = {
        "datetime": "API_DUMP_DATETIME",
        "api_version": "API_DUMP_VERSION",
        "status_code": "API_DUMP_STATUS_CODE",
        "response_ms": "API_DUMP_RESPONSE_MS",
        "total_count": "API_DUMP_TOTAL_COUNT",
    }

    for key, config_key in filters.items():
        if key in data and not get_config_or_model_meta(config_key, default=True):
            data.pop(key)

    # Optional: expose correlation id in body when explicitly enabled
    # Default is False (remain header-only via X-Request-ID)
    if "request_id" in data and not get_config_or_model_meta("API_DUMP_REQUEST_ID", default=False):
        data.pop("request_id")

    for key in ["next_url", "previous_url"]:
        if key in data and not data[key] and not get_config_or_model_meta(f"API_DUMP_NULL_{key.upper()}", default=True):
            data.pop(key)

    if "errors" in data and not data.get("errors") and not get_config_or_model_meta("API_DUMP_NULL_ERRORS", default=False):
        data.pop("errors")

    return data
