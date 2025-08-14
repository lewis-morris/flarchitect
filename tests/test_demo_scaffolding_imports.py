"""Unit tests for scaffolding config imports."""

from demo.scaffolding.module.config import Config


def test_config_import() -> None:
    """Config can be imported without triggering circular imports."""
    assert Config.API_TITLE == "Scaffolding API"
