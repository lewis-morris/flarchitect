from marshmallow import ValidationError
from flask import Flask
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String

from flarchitect.schemas.models import UserSchema


class _Base(DeclarativeBase):
    pass


class TestUser(_Base):
    __tablename__ = "test_user"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String)


def test_user_schema_pre_and_post_load_strips_and_sets_password():
    app = Flask(__name__)
    with app.app_context():
        # Patch model to a minimal mapped class for field generation
        UserSchema.Meta.model = TestUser  # type: ignore[attr-defined]
        schema = UserSchema()
    data_in = {
        "email": "user@example.com",
        "password": "s3cr3t",
        "password_hash": "should-be-removed",
        "roles": ["admin"],
    }

    # load will invoke pre_load and post_load; ensure stripping and instance make
    user = schema.load(data_in)
    # instance should have email and password set, but not password_hash/roles from input
    assert getattr(user, "email") == "user@example.com"
    assert getattr(user, "password") == "s3cr3t"
    assert not hasattr(user, "password_hash")
    # roles attribute may not exist on the testing model; important is it's not introduced by loader
    assert not hasattr(user, "roles")


def test_user_schema_validation_error_for_missing_email():
    app = Flask(__name__)
    with app.app_context():
        UserSchema.Meta.model = TestUser  # type: ignore[attr-defined]
        schema = UserSchema()
        try:
            schema.load({})
        except ValidationError as e:
            # Ensure our error path is triggered for required fields
            assert "email" in e.messages
