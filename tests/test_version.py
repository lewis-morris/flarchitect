from importlib.metadata import version as _get_version

from flarchitect import __version__


def test_version_matches_package() -> None:
    """Ensure the exposed version matches the installed package version."""
    assert __version__ == _get_version("flarchitect")
