"""Tests for rate limit service utilities."""

from __future__ import annotations

import pytest
from flask import Flask

from flarchitect.utils.general import (check_rate_prerequisites,
                                       check_rate_services)


class TestRateLimitServices:
    """Validate rate limit storage detection and prerequisites."""

    @staticmethod
    def _create_app(**config: str) -> Flask:
        app = Flask(__name__)
        app.config.update(config)
        return app

    def test_returns_config_uri(self) -> None:
        """Use configured storage URI when provided."""

        app = self._create_app(API_RATE_LIMIT_STORAGE_URI="redis://127.0.0.1:6379")
        with app.app_context():
            assert check_rate_services() == "redis://127.0.0.1:6379"

    def test_memory_storage_uri_allowed(self) -> None:
        """``memory://`` URIs do not require a host and should be accepted."""

        app = self._create_app(API_RATE_LIMIT_STORAGE_URI="memory://")
        with app.app_context():
            assert check_rate_services() == "memory://"

    def test_returns_none_without_services(self) -> None:
        """Return ``None`` when no cache services are reachable."""

        app = self._create_app()
        with app.app_context():
            assert check_rate_services() is None

    def test_prerequisites_missing_dependency(self) -> None:
        """Raise ``ImportError`` if required client library is absent."""

        with pytest.raises(ImportError):
            check_rate_prerequisites("Memcached")

    def test_invalid_storage_uri_raises(self) -> None:
        """Unsupported URI schemes raise a ``ValueError``."""

        app = self._create_app(API_RATE_LIMIT_STORAGE_URI="invalid://localhost")
        with app.app_context(), pytest.raises(ValueError):
            check_rate_services()

    def test_missing_host_in_storage_uri_raises(self) -> None:
        """A storage URI without a host should raise ``ValueError``."""

        app = self._create_app(API_RATE_LIMIT_STORAGE_URI="redis://")
        with app.app_context(), pytest.raises(ValueError):
            check_rate_services()
