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
