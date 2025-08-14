"""Tests for API endpoint description generation."""

from flask import Flask
from marshmallow import Schema

from flarchitect.specs.utils import make_endpoint_description


class UserSchema(Schema):
    """Schema used for testing."""


class Item:
    """Dummy parent model used for testing."""


def test_make_endpoint_description_parent_case() -> None:
    """The parent and child names should respect configured casing."""
    app = Flask(__name__)
    with app.app_context():
        desc = make_endpoint_description(UserSchema, "GET", parent=Item)
    assert desc == "Get a `user` by id for a specific `item`."
