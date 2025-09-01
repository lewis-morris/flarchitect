# Schema for loading login data (username and password)

from marshmallow import Schema, ValidationError, fields, validates


class LoginSchema(Schema):
    username = fields.String(required=True)
    password = fields.String(required=True)

    # Optional: Add custom validations for username or password, if needed
    @validates("username")
    def validate_username(self, value: str, **_: dict) -> None:
        """Ensure the username is present and sufficiently long.

        Args:
            value: The username provided by the user.
            _: Additional keyword arguments supplied by Marshmallow.

        Raises:
            ValidationError: If ``value`` is empty or shorter than three characters.
        """

        if not value:
            raise ValidationError("Username is required.")
        if len(value) < 3:
            raise ValidationError("Username must be at least 3 characters long.")

    @validates("password")
    def validate_password(self, value: str, **_: dict) -> None:
        """Ensure the password meets minimum requirements.

        Args:
            value: The password supplied by the user.
            _: Additional keyword arguments supplied by Marshmallow.

        Raises:
            ValidationError: If ``value`` is empty or shorter than six characters.
        """

        if not value:
            raise ValidationError("Password is required.")
        if len(value) < 6:
            raise ValidationError("Password must be at least 6 characters long.")


class TokenSchema(Schema):
    """Serialises access and refresh tokens with the user primary key."""

    access_token = fields.String(required=True)
    refresh_token = fields.String(required=True)
    user_pk = fields.String(required=True)


class RefreshSchema(Schema):
    """Validates refresh-token payloads."""

    refresh_token = fields.String(required=True)
