"""Persistent refresh token storage utilities.

This module defines a thread-safe API for persisting JWT refresh tokens
with their associated metadata. Tokens are stored in a database table
using SQLAlchemy, allowing the application to invalidate refresh tokens
and track their expiration.
"""

from __future__ import annotations

import datetime
from threading import Lock

from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from flarchitect.utils.session import get_session


class Base(DeclarativeBase):
    """Base declarative class for refresh token models."""


class RefreshToken(Base):
    """SQLAlchemy model representing a stored refresh token."""

    __tablename__ = "refresh_tokens"

    token: Mapped[str] = mapped_column(String, primary_key=True)
    user_pk: Mapped[str] = mapped_column(String, nullable=False)
    user_lookup: Mapped[str] = mapped_column(String, nullable=False)
    expires_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


_lock = Lock()
_table_created = False


def _ensure_table(session: Session) -> None:
    """Create the refresh token table if it does not exist."""
    global _table_created
    if not _table_created:
        RefreshToken.metadata.create_all(bind=session.get_bind())
        _table_created = True


def store_refresh_token(
    token: str, user_pk: str, user_lookup: str, expires_at: datetime.datetime
) -> None:
    """Persist a refresh token and its metadata.

    Args:
        token: Encoded refresh token string.
        user_pk: User primary key value as a string.
        user_lookup: User lookup field value as a string.
        expires_at: Token expiration timestamp.
    """
    with _lock:
        session = get_session(RefreshToken)
        _ensure_table(session)
        session.merge(
            RefreshToken(
                token=token,
                user_pk=user_pk,
                user_lookup=user_lookup,
                expires_at=expires_at,
            )
        )
        session.commit()


def get_refresh_token(token: str) -> RefreshToken | None:
    """Retrieve a stored refresh token.

    Args:
        token: Encoded refresh token string.

    Returns:
        RefreshToken | None: Stored refresh token or ``None`` if not found.
    """
    session = get_session(RefreshToken)
    _ensure_table(session)
    session.expire_all()
    return session.get(RefreshToken, token)


def delete_refresh_token(token: str) -> None:
    """Remove a refresh token from storage in a thread-safe manner.

    Args:
        token: Encoded refresh token string.
    """
    with _lock:
        session = get_session(RefreshToken)
        _ensure_table(session)
        instance = session.get(RefreshToken, token)
        if instance is not None:
            session.delete(instance)
            session.commit()
            session.expire_all()
