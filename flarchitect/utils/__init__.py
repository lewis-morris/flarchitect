"""Utility helpers for flarchitect.

Expose selected submodules to simplify dotted-path monkeypatching in tests,
e.g. "flarchitect.utils.session.get_config_or_model_meta" and
"flarchitect.utils.response_filters.get_config_or_model_meta".
"""

from . import response_filters as response_filters  # expose for monkeypatching
from . import session as session  # make submodule available as attribute
from . import cookies as cookies  # expose cookie helpers for blueprints
from . import sse as sse  # SSE utilities for event streams
from .cookies import cookie_settings
from .session import get_session  # re-export convenience
from .sse import model_event, sse_message, stream_model_events, stream_sse_response

__all__ = [
    "get_session",
    "session",
    "response_filters",
    "cookies",
    "cookie_settings",
    "sse",
    "sse_message",
    "model_event",
    "stream_sse_response",
    "stream_model_events",
]
