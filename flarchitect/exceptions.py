import traceback
from http import HTTPStatus
from typing import Any

from flask import Response, request
from werkzeug.exceptions import HTTPException

from flarchitect.utils.config_helpers import get_config_or_model_meta
from flarchitect.utils.response_helpers import create_response


class CustomHTTPException(HTTPException):
    """Custom HTTP exception that mirrors :class:`werkzeug.exceptions.HTTPException`.

    The class stores a status code and optional reason, exposing them in a
    dictionary friendly format via :meth:`to_dict`. Subclassing
    :class:`HTTPException` ensures Flask's error handling machinery treats the
    exception consistently with built-in HTTP exceptions.
    """

    def __init__(self, status_code: int, reason: str | None = None) -> None:
        """Initialise the exception.

        Args:
            status_code: HTTP status code associated with the error.
            reason: Optional human readable reason for the error.
        """
        self.code = status_code
        self.description = reason or HTTPStatus(status_code).phrase
        self.status_code = status_code
        self.error = HTTPStatus(status_code).phrase
        self.reason = self.description
        super().__init__(description=self.description)

    @property
    def name(self) -> str:  # pragma: no cover - simple property
        """Return the HTTP status phrase for the error."""
        return HTTPStatus(self.code).phrase

    def to_dict(self) -> dict[str, int | str | None]:
        """Serialise the exception to a dictionary."""
        return {
            "status_code": self.status_code,
            "status_text": self.error,
            "reason": self.reason,
        }


def handle_http_exception(e: HTTPException) -> Response:
    """
    Handles HTTP exceptions and returns a standardised response.

    Args:
        e (HTTPException): The HTTP exception instance.

    Returns:
        Response: A standardised response object.
    """
    if get_config_or_model_meta(key="API_PRINT_EXCEPTIONS", default=True):
        _print_exception(e)

    prefix = get_config_or_model_meta("API_PREFIX", default="/api")
    if request.path.startswith(prefix):
        return create_response(status=e.code, errors={"error": e.name, "reason": e.description})

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


def _handle_exception(error: str, status_code: int, error_name: str | None = None, print_exc: bool = True) -> Any:
    """Handles exceptions and formats them into a standardised response."""
    if print_exc:
        import traceback

        traceback.print_exc()

    return create_response(
        status=status_code,
        errors={
            "error": error,
            "reason": error_name,
        },  # Structured error payload for consistent responses
    )


__all__ = ["CustomHTTPException", "_print_exception", "handle_http_exception", "_handle_exception"]
