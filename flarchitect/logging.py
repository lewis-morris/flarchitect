import re

from colorama import Fore, Style, init

# Initialize Colorama
init(autoreset=True)


def color_text_with_multiple_patterns(text):
    """Color text wrapped in specific patterns with respective colors."""

    # Patterns to match text: backticks, hyphens, pluses, dollars, and pipes
    patterns = {
        r"`(.*?)`": (Fore.YELLOW, Style.NORMAL),  # Yellow for backticks
        r"\+(.*?)\+": (Fore.RED, Style.NORMAL),  # Red for pluses
        r"--(.*?)--": (Fore.CYAN, Style.NORMAL),  # Cyan for hyphens
        r"\$(.*?)\$": (Fore.MAGENTA, Style.BRIGHT),  # Magenta for dollars
        r"\|(.*?)\|": (Fore.GREEN, Style.BRIGHT),  # Green for pipes
    }

    # Function to replace matched text with colored version
    def replace_with_color(match, color, style):
        return color + style + match.group(1) + Style.RESET_ALL

    # Iterate over the patterns and apply each one
    for pattern, (color, style) in patterns.items():
        # Pass both color and style to the lambda function
        text = re.sub(
            pattern, lambda match: replace_with_color(match, color, style), text
        )

    return text


class CustomLogger:
    def __init__(self, verbosity_level=0):
        self.verbosity_level = verbosity_level

    def _log(self, text: str):
        """
        Log a message to the console.
        Args:
            text (str): The message to log.

        Returns:
            None
        """
        print(color_text_with_multiple_patterns(text))

    def log(self, level, message):
        """Log a message if its level is less than or equal to the current verbosity level."""
        if level <= self.verbosity_level:
            self._log(f"LOG {level}: ".ljust(10) + message)

    def debug(self, level, message):
        """Log a message if its level is less than or equal to the current verbosity level."""
        if level <= self.verbosity_level:
            self._log(f"DEBUG {level}: ".ljust(10) + message)

    def error(self, level, message):
        """Log a message if its level is less than or equal to the current verbosity level."""
        if level <= self.verbosity_level:
            self._log(
                Fore.RED + f"ERROR {level}: ".ljust(10) + Style.RESET_ALL + message
            )


logger = CustomLogger()
