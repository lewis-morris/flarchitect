"""Custom logging utilities providing coloured or JSON logs with verbosity control.

Adds optional structured JSON output enriched with request context when
running under Flask. Falls back to colourised human-friendly output.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any

try:
    # Flask may not always be present; guard imports.
    from flask import g, has_request_context, request
except Exception:  # pragma: no cover - optional import for non-Flask usage
    def has_request_context() -> bool:  # type: ignore
        return False

    request = None  # type: ignore
    g = None  # type: ignore

from colorama import Fore, Style, init

# Initialise Colorama
init(autoreset=True)


def color_text_with_multiple_patterns(text: str) -> str:
    """Colour text wrapped in specific patterns with respective colours.

    Args:
        text: The text containing wrapped patterns.

    Returns:
        The colourised text with patterns replaced.
    """
    patterns: dict[str, tuple[str, str]] = {
        r"`(.*?)`": (Fore.YELLOW, Style.NORMAL),  # Yellow for backticks
        r"\+(.*?)\+": (Fore.RED, Style.NORMAL),  # Red for pluses
        r"--(.*?)--": (Fore.CYAN, Style.NORMAL),  # Cyan for hyphens
        r"\$(.*?)\$": (Fore.MAGENTA, Style.BRIGHT),  # Magenta for dollars
        r"\|(.*?)\|": (Fore.GREEN, Style.BRIGHT),  # Green for pipes
    }

    def replace_with_color(match: re.Match[str], color: str, style: str) -> str:
        return f"{color}{style}{match.group(1)}{Style.RESET_ALL}"

    for pattern, (color, style) in patterns.items():
        text = re.sub(
            pattern,
            lambda match, color=color, style=style: replace_with_color(match, color, style),
            text,
        )

    return text


class CustomLogger:
    """Simple logger with verbosity-based level control and JSON mode."""

    def __init__(self, verbosity_level: int = 0) -> None:
        self.verbosity_level = verbosity_level
        self.json_mode: bool = False

    def _emit_text(self, text: str) -> None:
        print(color_text_with_multiple_patterns(text))

    def _emit_json(self, payload: dict[str, Any]) -> None:
        print(json.dumps(payload, separators=(",", ":")))

    def _context(self) -> dict[str, Any]:
        if has_request_context():  # pragma: no cover - integration behaviour
            ctx: dict[str, Any] = {
                "method": request.method,
                "path": request.path,
            }
            # Best-effort request id and timing
            try:
                ctx["request_id"] = getattr(g, "request_id", None)
                start = getattr(g, "_flarch_req_start", None)
                if start is not None:
                    ctx["latency_ms"] = int((time.perf_counter() - start) * 1000)
            except Exception:
                pass
            return ctx
        return {}

    def _log_with_prefix(self, level: int, message: str, prefix: str, color: str | None = None) -> None:
        """Internal helper to log with a prefix and optional colour or JSON."""
        if level <= self.verbosity_level:
            if self.json_mode:
                payload = {
                    "event": prefix.lower(),
                    "lvl": level,
                    "message": message,
                }
                payload.update(self._context())
                self._emit_json(payload)
            else:
                prefix_text = f"{prefix} {level}: ".ljust(10)
                if color:
                    prefix_text = f"{color}{prefix_text}{Style.RESET_ALL}"
                self._emit_text(prefix_text + message)

    def log(self, level: int, message: str) -> None:
        """Log a message if its level is less than or equal to the current verbosity level."""
        self._log_with_prefix(level, message, "LOG")

    def debug(self, level: int, message: str) -> None:
        """Log a debug message if its level is less than or equal to the current verbosity level."""
        self._log_with_prefix(level, message, "DEBUG")

    def error(self, level: int, message: str) -> None:
        """Log an error message if its level is less than or equal to the current verbosity level."""
        self._log_with_prefix(level, message, "ERROR", color=Fore.RED)


logger = CustomLogger()

def get_logger() -> CustomLogger:
    """Return the module-level logger instance."""
    return logger
