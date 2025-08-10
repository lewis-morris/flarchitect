import traceback
from http import HTTPStatus
from typing import Any

from flask import Response, request
from werkzeug.exceptions import HTTPException

from flarchitect.utils.config_helpers import get_config_or_model_meta
from flarchitect.utils.response_helpers import create_response


class CustomHTTPException(Exception):
    """
    Custom HTTP Exception class
    """

    status_code = None
    error = None
    reason = None

    def __init__(self, status_code, reason=None):
        """
        A custom HTTP exception class

        Args:
            status_code (int): HTTP status code
            reason (str): Reason for the HTTP status code
        """
        self.status_code = status_code
        self.error = HTTPStatus(
            status_code
        ).phrase  # Fetch the standard HTTP status phrase
        self.reason = (
            reason or self.error
        )  # Use the reason if provided, otherwise use the standard HTTP status phrase

    def to_dict(self):
        return {
            "status_code": self.status_code,
            "status_text": self.error,
            "reason": self.reason,
        }


def handle_http_exception(e: HTTPException) -> Response:
    """
    Handles HTTP exceptions and returns a standardized response.

    Args:
        e (HTTPException): The HTTP exception instance.

    Returns:
        Response: A standardized response object.
    """
    if get_config_or_model_meta(key="API_PRINT_EXCEPTIONS", default=True):
        _print_exception(e)

    prefix = get_config_or_model_meta("API_PREFIX", default="/api")
    if request.path.startswith(prefix):
        return create_response(
            status=e.code, errors={"error": e.name, "reason": e.description}
        )

    # If not an API route, re-raise the exception to let Flask handle it
    return e


def _print_exception(e: Exception) -> None:
    """
    Prints the exception message and stack trace if configured to do so.

    Args:
        e (Exception): The exception to print.
    """
    print(e)
    traceback.print_exc()


def _handle_exception(
    error: str, status_code: int, error_name: str | None = None, print_exc: bool = True
) -> Any:
    """Handles exceptions and formats them into a standardized response."""
    if print_exc:
        import traceback

        traceback.print_exc()

    return create_response(
        status=status_code,
        errors={
            "error": error,
            "reason": error_name,
        },  # changed this in an attempt to make errors more uniform ##[{"status_text": error_name or "Error", "error": error}]
    )
