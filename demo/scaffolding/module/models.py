"""Database models for the scaffolding application with advanced options."""

from __future__ import annotations

from flask import current_app
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from validators import email as validate_email
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


def _titleize_name(obj: Item) -> Item:
    """Ensure item names are title-cased before saving."""

    obj.name = obj.name.title()
    return obj


class Category(db.Model):
    """Grouping for items to demonstrate nested writes."""

    __tablename__ = "category"

    class Meta:
        tag_group = "Core"
        tag = "Categories"
        allow_nested_writes = True
        description = {
            "GET": "Retrieve categories and their items.",
            "POST": "Create a new category.",
        }

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(80), unique=True, nullable=False, info={"description": "Category name"})

    items: Mapped[list[Item]] = relationship(back_populates="category")

    @validates("name")
    def validate_name(self, _key: str, value: str) -> str:
        """Ensure category names are not empty."""

        if not value.strip():
            raise ValueError("Category name cannot be empty")
        return value.strip()


class User(db.Model):
    """User account model with validation and password helpers."""

    __tablename__ = "user"

    class Meta:
        tag_group = "Core"
        tag = "Users"
        allow_nested_writes = False
        allowed_methods = ["GET", "POST"]
        post_rate_limit = "5 per minute"
        description = {
            "GET": "Retrieve users.",
            "POST": "Create a new user.",
        }

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(db.String(80), unique=True, nullable=False, info={"description": "Unique username"})
    email: Mapped[str] = mapped_column(
        db.String(120),
        unique=True,
        nullable=False,
        info={
            "description": "User email address.",
            "format": "email",
            "validator": "email",
            "validator_message": "Invalid email address.",
        },
    )
    website: Mapped[str | None] = mapped_column(db.String(255), info={"description": "User website", "format": "uri"})
    password_hash: Mapped[str] = mapped_column(db.String(128), nullable=False)

    items: Mapped[list[Item]] = relationship(back_populates="owner")

    @validates("email")
    def validate_email(self, _key: str, address: str) -> str:
        """Ensure e-mail addresses are valid."""

        if not validate_email(address):
            raise ValueError("Invalid email address")
        return address

    @validates("username")
    def validate_username(self, _key: str, username: str) -> str:
        """Validate username length from configuration."""

        min_len = int(current_app.config.get("USERNAME_MIN_LENGTH", 3))
        if len(username) < min_len:
            raise ValueError(f"Username must be at least {min_len} characters long")
        return username

    def set_password(self, password: str) -> None:
        """Hash and store the user's password."""

        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check a password against the stored hash."""

        return check_password_hash(self.password_hash, password)


class Item(db.Model):
    """Example model representing a user-owned item."""

    __tablename__ = "item"

    class Meta:
        tag_group = "Core"
        tag = "Items"
        allow_nested_writes = True
        add_callback = staticmethod(lambda obj, model: _titleize_name(obj))
        description = {
            "GET": "Retrieve items with their owners and categories.",
            "POST": "Create an item, optionally with its category.",
            "PATCH": "Update an item's details.",
        }
        patch_rate_limit = "10 per minute"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(120), nullable=False, info={"description": "Item name"})
    price: Mapped[float | None] = mapped_column(db.Numeric(10, 2), nullable=True, info={"description": "Item price", "example": 9.99})
    owner_id: Mapped[int] = mapped_column(db.ForeignKey("user.id"), nullable=False)
    owner: Mapped[User] = relationship(back_populates="items")
    category_id: Mapped[int | None] = mapped_column(db.ForeignKey("category.id"), nullable=True)
    category: Mapped[Category | None] = relationship(back_populates="items")

    @validates("price")
    def validate_price(self, _key: str, value: float | None) -> float | None:
        """Ensure prices are positive."""

        if value is not None and value < 0:
            raise ValueError("Price must be positive")
        return value
