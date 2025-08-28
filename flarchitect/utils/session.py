"""Utilities for resolving SQLAlchemy sessions.

This module provides :func:`get_session`, a helper that tries to
locate the active :class:`sqlalchemy.orm.Session` object used by the
application. It supports both ``Flask-SQLAlchemy`` and plain SQLAlchemy
setups so that models do not need to implement their own
``get_session`` method.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager, suppress

from flask import current_app
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from flarchitect.utils.config_helpers import get_config_or_model_meta


def _resolve_session(model: type[DeclarativeBase] | None = None) -> Session:
    """Resolve an active SQLAlchemy session for the given model.

    This function contains the session resolution logic and is used internally
    by :func:`get_session`.

    Args:
        model: Optional SQLAlchemy declarative model used when searching for a
            session.

    Returns:
        Session: The resolved SQLAlchemy session instance.

    Raises:
        RuntimeError: If no session can be determined.
    """

    # 1. Configurable getter from Flask config or model meta
    try:
        custom_getter: Callable[[], Session] | None = get_config_or_model_meta("API_SESSION_GETTER", model=model, default=None)
        if callable(custom_getter):
            session = custom_getter()
            if session is not None:
                return session
    except Exception:  # pragma: no cover - defensive
        pass

    # 2. Flask-SQLAlchemy global session
    try:  # pragma: no cover - only executed when Flask context exists
        ext = current_app.extensions.get("sqlalchemy")  # type: ignore[attr-defined]
        if ext is not None:
            session = getattr(ext, "session", None)
            if session is not None:
                return session
    except Exception:  # pragma: no cover - defensive
        pass

    if model is not None:
        # 3. SQLAlchemy model bound session via query attribute
        query = getattr(model, "query", None)
        session = getattr(query, "session", None)
        if session is not None:
            return session

        # 4. Legacy ``get_session`` method on the model
        legacy_getter = getattr(model, "get_session", None)
        if callable(legacy_getter):
            session = legacy_getter()
            if session is not None:
                return session

        # 5. Create a session from the model's bound engine
        engine = getattr(getattr(model, "__table__", None), "metadata", None)
        engine = getattr(engine, "bind", None)
        if engine is None:
            engine = getattr(getattr(model, "metadata", None), "bind", None)
        if engine is not None:
            SessionMaker = sessionmaker(bind=engine)
            return SessionMaker()

    raise RuntimeError("Unable to determine database session; configure API_SESSION_GETTER or bind an engine.")


@contextmanager
def get_session(model: type[DeclarativeBase] | None = None) -> Iterator[Session]:
    """Yield the active SQLAlchemy :class:`~sqlalchemy.orm.Session`.

    The session is resolved using :func:`_resolve_session` and is automatically
    closed when the context manager exits.

    Args:
        model: Optional SQLAlchemy declarative model used when searching for a
            session.

    Yields:
        Session: The resolved SQLAlchemy session instance.

    Raises:
        RuntimeError: If no session can be determined.
    """

    session = _resolve_session(model)
    try:
        yield session
    finally:
        with suppress(Exception):  # pragma: no cover - defensive
            session.close()
