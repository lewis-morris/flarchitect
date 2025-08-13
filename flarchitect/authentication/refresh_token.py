from __future__ import annotations

import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from flarchitect.utils.config_helpers import get_config_or_model_meta


class Base(DeclarativeBase):
    """Base class for refresh token models."""


class RefreshToken(Base):
    """Persistent refresh token model for JWT authentication."""

    __tablename__ = "refresh_tokens"

    token: Mapped[str] = mapped_column(String, primary_key=True)
    user_lookup: Mapped[str] = mapped_column(String, nullable=False)
    user_pk: Mapped[str] = mapped_column(String, nullable=False)
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    @staticmethod
    def get_session() -> Session:
        """Return the configured SQLAlchemy session.

        Returns:
            Session: Active SQLAlchemy session tied to the user model.
        """
        usr_model = get_config_or_model_meta("API_USER_MODEL")
        return usr_model.get_session()
