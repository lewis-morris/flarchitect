from typing import Any

from marshmallow import Schema, fields, post_load, pre_load
from sqlalchemy.testing.pickleable import User

from flarchitect.schemas.bases import AutoSchema


class DeleteSuccessfulSchema(Schema):
    class Meta:
        name = "delete-success"

    # Successful Delete
    message = fields.Str(required=True)


class LoginInputSchema(Schema):
    """
    Schema for the login route, this is used to validate the data sent to the route.
    """

    class Meta:
        dump = False
        name = "login"

    email = fields.Str(
        required=True,
        load_only=True,
        metadata={
            "description": "Users email address",
            "type": "string",
            "format": "email",
        },
    )
    password = fields.Str(
        required=True,
        load_only=True,
        metadata={
            "description": "Users password",
            "type": "string",
            "format": "password",
        },
    )


class ResetPasswordSchemaIn(Schema):
    class Meta:
        name = "reset-password"

    email = fields.Str(
        required=True,
        load_only=True,
        metadata={
            "description": "Users email address",
            "type": "string",
            "format": "email",
        },
    )


class ResetPasswordSchemaOut(Schema):
    class Meta:
        name = "reset-password-success"

    message = fields.Str(
        dump_only=True,
        metadata={
            "description": "Response message",
            "type": "string",
            "format": "email",
        },
    )


class UserSchema(AutoSchema):
    class Meta:
        name = "user"
        model = User

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @pre_load
    def remove_unwanted_fields(self, data: dict[str, Any], **kwargs) -> dict[str, Any]:
        """Strip fields that should not be provided by clients.

        Removes ``password_hash`` and ``roles`` to protect server-managed
        attributes. If a ``password`` is supplied it is temporarily stored and
        removed from the payload so it can be set via the model's password
        setter.
        """
        if "password_hash" in data:
            data.pop("password_hash", None)
        if "roles" in data:
            data.pop("roles", None)
        if "password" in data:
            self.password = data.pop("password", None)

        return data

    password = fields.Str(required=False)

    @post_load
    def make_instance(self, data: dict[str, Any], **kwargs) -> User:
        """Create a ``User`` instance from validated data.

        Args:
            data: The data to be loaded.
            **kwargs: Additional keyword arguments.

        Returns:
            User: Model instance with attributes assigned. If a password was
            provided it is set using the model's password setter.
        """
        instance = self.Meta.model(**data)

        for key, value in data.items():
            setattr(instance, key, value)

        if hasattr(self, "password"):
            instance.password = self.password

        return instance


class TokenRefreshSchema(Schema):
    class Meta:
        name = "token-refresh"

    access_token = fields.Str(
        required=True,
        dump_only=True,
        metadata={
            "description": "Access token",
            "type": "string",
            "format": "password",
        },
    )

    refresh_token = fields.Str(
        required=True,
        dump_only=True,
        metadata={
            "description": "Refresh token",
            "type": "string",
            "format": "password",
        },
    )
    user = fields.Nested(UserSchema, dump_only=True)


class RefreshInputSchema(Schema):
    class Meta:
        dump = False
        name = "refresh-token"

    refresh_token = fields.Str(
        required=True,
        load_only=True,
        metadata={
            "description": "Refresh token",
            "type": "string",
            "format": "password",
        },
    )


class RefreshOutputSchema(Schema):
    class Meta:
        name = "refresh-token-success"

    access_token = fields.Str(
        required=True,
        dump_only=True,
        metadata={
            "description": "Access token",
            "type": "string",
            "format": "password",
        },
    )
