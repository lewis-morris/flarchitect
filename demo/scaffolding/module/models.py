"""Database models for the scaffolding application."""

from __future__ import annotations

from flask import current_app
from sqlalchemy.orm import validates
from validators import email as validate_email
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


class User(db.Model):
    """User account model."""

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    @validates("email")
    def validate_email(self, key: str, address: str) -> str:
        """Ensure e-mail addresses are valid."""

        if not validate_email(address):
            raise ValueError("Invalid email address")
        return address

    @validates("username")
    def validate_username(self, key: str, username: str) -> str:
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

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    owner = db.relationship("User", backref="items")
