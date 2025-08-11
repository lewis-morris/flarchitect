"""Example callback functions for the callbacks demo application."""

from __future__ import annotations

from typing import Any


def setup_callback(*, model, **kwargs) -> dict[str, Any]:
    """Example setup callback used in the demo.

    Args:
        model: The model class being accessed.
        **kwargs: Additional keyword arguments passed from the framework.

    Returns:
        Dict[str, Any]: Potentially modified keyword arguments.
    """
    return kwargs


def return_callback(*, model, output, **kwargs) -> dict[str, Any]:
    """Example return callback used in the demo.

    Args:
        model: The model class being accessed.
        output: The value returned from the database operation.
        **kwargs: Additional keyword arguments.

    Returns:
        Dict[str, Any]: A dictionary containing the ``output`` key.
    """
    return {"output": output}


def final_callback(data: dict[str, Any]) -> dict[str, Any]:
    """Attach a marker before the response is sent."""
    data["finalized"] = True
    return data


def error_callback(error: str, status_code: int, value: Any) -> None:
    """Handle errors raised during a request."""
    _ = (error, status_code, value)  # Placeholder for real logging.


def dump_callback(data: dict[str, Any], **kwargs) -> dict[str, Any]:
    """Modify serialised data prior to returning it to the client."""
    data["demo"] = True
    return data
