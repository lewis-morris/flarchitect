"""Application loader for the scaffolding example."""

from flask import Flask

from .module import create_app


def load(config_class: str = "demo.scaffolding.config.Config") -> Flask:
    """Create and return a configured Flask application.

    Args:
        config_class: Dotted path to the configuration object.

    Returns:
        Configured ``flask.Flask`` application.
    """

    return create_app(config_class)


if __name__ == "__main__":
    app = load()
    app.run(host="0.0.0.0", port=5000, debug=True)
