"""Tests for scaffolding demo models with advanced options."""

from demo.scaffolding.module import create_app
from demo.scaffolding.module.extensions import db
from demo.scaffolding.module.models import Category, Item, User, _titleize_name


def test_base_model_fields() -> None:
    app = create_app()
    with app.app_context():
        user = User(username="alice", email="alice@example.com")
        user.set_password("secret")
        db.session.add(user)
        db.session.flush()
        assert user.created is not None
        assert user.updated is not None
        assert user.deleted is False


def test_item_add_callback_titleizes_name() -> None:
    item = Item(name="some item", owner_id=1)
    _titleize_name(item)
    assert item.name == "Some Item"


def test_category_allows_nested_writes() -> None:
    assert Category.Meta.allow_nested_writes is True
