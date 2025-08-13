"""Custom logging utilities providing colored pattern highlighting and verbosity control."""

from __future__ import annotations

import re

from colorama import Fore, Style, init

# Initialize Colorama
init(autoreset=True)


def color_text_with_multiple_patterns(text: str) -> str:
    """Color text wrapped in specific patterns with respective colors.

    Args:
        text: The text containing wrapped patterns.

    Returns:
        The colorized text with patterns replaced.
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
    """Simple logger with verbosity-based level control."""

    def __init__(self, verbosity_level: int = 0) -> None:
        self.verbosity_level = verbosity_level

    def _log(self, text: str) -> None:
        """Log a message to the console.

        Args:
            text: The message to log.
        """
        print(color_text_with_multiple_patterns(text))

    def _log_with_prefix(self, level: int, message: str, prefix: str, color: str | None = None) -> None:
        """Internal helper to log with a prefix and optional color."""
        if level <= self.verbosity_level:
            prefix_text = f"{prefix} {level}: ".ljust(10)
            if color:
                prefix_text = f"{color}{prefix_text}{Style.RESET_ALL}"
            self._log(prefix_text + message)

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
