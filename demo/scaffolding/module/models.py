"""Database models for the scaffolding application."""

from __future__ import annotations

from flask import current_app
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from validators import email as validate_email
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


class User(db.Model):
    """User account model with basic validation and password helpers."""

    __tablename__ = "user"

    class Meta:
        tag_group = "Core"
        tag = "Users"
        allow_nested_writes = False

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(db.String(80), unique=True, nullable=False, info={"description": "Unique username"})
    email: Mapped[str] = mapped_column(db.String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(db.String(128), nullable=False)

    items: Mapped[list[Item]] = relationship(back_populates="owner")

    @validates("email")
    def validate_email(self, _key: str, address: str) -> str:
        """Ensure e-mail addresses are valid.

        Args:
            _key: Field name being validated.
            address: E-mail address to validate.

        Raises:
            ValueError: If ``address`` is not a valid e-mail.

        Returns:
            A verified e-mail address.
        """

        if not validate_email(address):
            raise ValueError("Invalid email address")
        return address

    @validates("username")
    def validate_username(self, _key: str, username: str) -> str:
        """Validate username length from configuration.

        Args:
            _key: Field name being validated.
            username: Proposed username.

        Raises:
            ValueError: If ``username`` is shorter than the configured minimum.

        Returns:
            The validated username.
        """

        min_len = int(current_app.config.get("USERNAME_MIN_LENGTH", 3))
        if len(username) < min_len:
            raise ValueError(f"Username must be at least {min_len} characters long")
        return username

    def set_password(self, password: str) -> None:
        """Hash and store the user's password.

        Args:
            password: Plain-text password to hash.
        """

        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check a password against the stored hash.

        Args:
            password: Plain-text candidate password.

        Returns:
            ``True`` if the password matches the stored hash.
        """

        return check_password_hash(self.password_hash, password)


class Item(db.Model):
    """Example model representing a user-owned item."""

    __tablename__ = "item"

    class Meta:
        tag_group = "Core"
        tag = "Items"
        allow_nested_writes = True

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(120), nullable=False, info={"description": "Item name"})
    owner_id: Mapped[int] = mapped_column(db.ForeignKey("user.id"), nullable=False)
    owner: Mapped[User] = relationship(back_populates="items")
