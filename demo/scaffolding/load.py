"""Application loader for the scaffolding example."""

from flask import Flask

from .module import create_app


def load(config_class: str = "Scaffolding.config.Config") -> Flask:
    """Create and return a configured Flask application.

    Args:
        config_class: Dotted path to the configuration object.

    Returns:
        Configured :class:`flask.Flask` application.
    """

    return create_app(config_class)


if __name__ == "__main__":
    """Run the application if this module is executed directly."""
    app = load()
    app.run(host="0.0.0.0", port=5000, debug=True)