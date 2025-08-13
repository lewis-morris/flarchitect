import datetime
import os
from typing import Any

import jwt
from flask import current_app
from sqlalchemy.exc import NoResultFound

from flarchitect.database.utils import get_primary_keys
from flarchitect.exceptions import CustomHTTPException
from flarchitect.utils.config_helpers import get_config_or_model_meta
from flarchitect.utils.session import get_session

# Secret keys (keep them secure)


# In-memory store for refresh tokens (use a persistent database in production)
refresh_tokens_store: dict[str, dict[str, Any]] = {}


def get_pk_and_lookups() -> tuple[str, str]:
    """Retrieve the primary key name and lookup field for the user model.

    Returns:
        tuple[str, str]: A tuple of the primary key field name and the lookup
        field configured for the user model.

    Raises:
        CustomHTTPException: If the user model or lookup field configuration is
        missing.
    """

    lookup_field = get_config_or_model_meta("API_USER_LOOKUP_FIELD")
    usr = get_config_or_model_meta("API_USER_MODEL")
    primary_keys = get_primary_keys(usr)
    return primary_keys.name, lookup_field


def generate_access_token(usr_model: Any, expires_in_minutes: int = 360) -> str:
    """Create a short-lived JSON Web Token for the given user.

    Args:
        usr_model (Any): The user model instance for which to create the token.
        expires_in_minutes (int, optional): Token lifetime in minutes.
            Defaults to ``360``.

    Returns:
        str: The encoded JWT access token.

    Raises:
        CustomHTTPException: If the access secret key is not configured.
    """

    pk, lookup_field = get_pk_and_lookups()

    ACCESS_SECRET_KEY = os.environ.get("ACCESS_SECRET_KEY") or current_app.config.get("ACCESS_SECRET_KEY")
    if ACCESS_SECRET_KEY is None:
        raise CustomHTTPException(status_code=500, reason="ACCESS_SECRET_KEY missing")

    payload = {
        lookup_field: str(getattr(usr_model, lookup_field)),  # Convert UUID to string
        pk: str(getattr(usr_model, pk)),  # Convert UUID to string
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=expires_in_minutes),
        "iat": datetime.datetime.now(datetime.timezone.utc),
    }
    token = jwt.encode(payload, ACCESS_SECRET_KEY, algorithm="HS256")
    return token


def generate_refresh_token(usr_model: Any, expires_in_days: int = 2) -> str:
    """Create a long-lived refresh token for the given user.

    Args:
        usr_model (Any): The user model instance for which to create the token.
        expires_in_days (int, optional): Token lifetime in days. Defaults to ``2``.

    Returns:
        str: The encoded JWT refresh token.

    Raises:
        CustomHTTPException: If the refresh secret key is not configured.
    """

    REFRESH_SECRET_KEY = os.environ.get("REFRESH_SECRET_KEY") or current_app.config.get("REFRESH_SECRET_KEY")
    if REFRESH_SECRET_KEY is None:
        raise CustomHTTPException(status_code=500, reason="REFRESH_SECRET_KEY missing")

    pk, lookup_field = get_pk_and_lookups()

    payload = {
        lookup_field: str(getattr(usr_model, lookup_field)),  # Convert UUID to string
        pk: str(getattr(usr_model, pk)),  # Convert UUID to string
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=expires_in_days),
        "iat": datetime.datetime.now(datetime.timezone.utc),
    }
    token = jwt.encode(payload, REFRESH_SECRET_KEY, algorithm="HS256")

    # Store the refresh token in the server-side store
    refresh_tokens_store[token] = {
        lookup_field: str(getattr(usr_model, lookup_field)),  # Convert UUID to string
        pk: str(getattr(usr_model, pk)),  # Convert UUID to string
        "expires_at": payload["exp"],
    }
    return token


def decode_token(token: str, secret_key: str) -> dict[str, Any]:
    """Decode a JWT and return its payload.

    Args:
        token (str): The encoded JWT.
        secret_key (str): The secret key used to decode the token.

    Returns:
        dict[str, Any]: The decoded token payload.

    Raises:
        CustomHTTPException: If the token is expired or invalid.
    """

    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError as exc:
        raise CustomHTTPException(status_code=401, reason="Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise CustomHTTPException(status_code=401, reason="Invalid token") from exc


def refresh_access_token(refresh_token: str) -> tuple[str, Any]:
    """Use a refresh token to issue a new access token.

    Args:
        refresh_token (str): The JWT refresh token.

    Returns:
        tuple[str, Any]: A tuple containing the new access token and the user
        object.

    Raises:
        CustomHTTPException: If the token is invalid, expired, or the user cannot
        be found.
    """
    # Verify refresh token
    REFRESH_SECRET_KEY = os.environ.get("REFRESH_SECRET_KEY") or current_app.config.get("REFRESH_SECRET_KEY")
    payload = decode_token(refresh_token, REFRESH_SECRET_KEY)
    if payload is None:
        raise CustomHTTPException(status_code=401, reason="Invalid token")

    # Check if the refresh token is in the store and not expired
    stored_token = refresh_tokens_store.get(refresh_token)
    if not stored_token or datetime.datetime.now(datetime.timezone.utc) > stored_token["expires_at"]:
        raise CustomHTTPException(status_code=403, reason="Invalid or expired refresh token")

    # Get user identifiers from stored_token
    pk_field, lookup_field = get_pk_and_lookups()
    lookup_value = stored_token.get(lookup_field)
    pk_value = stored_token.get(pk_field)

    # Get the user model (this is the SQLAlchemy model)
    usr_model_class = get_config_or_model_meta("API_USER_MODEL")

    # Query the user by lookup_field and pk
    try:
        user = (
            get_session(usr_model_class)
            .query(usr_model_class)
            .filter(
                getattr(usr_model_class, lookup_field) == lookup_value,
                getattr(usr_model_class, pk_field) == pk_value,
            )
            .one()
        )
    except NoResultFound as exc:
        raise CustomHTTPException(status_code=404, reason="User not found") from exc

    # Generate new access token
    new_access_token = generate_access_token(user)

    refresh_tokens_store.pop(refresh_token)

    return new_access_token, user


def get_user_from_token(token: str, secret_key: str | None = None) -> Any:
    """Decode a token and return the associated user.

    Args:
        token (str): The JWT containing user information.
        secret_key (str | None, optional): The secret key used to decode the
            token. If ``None``, the access secret key is used.

    Returns:
        Any: The user model instance corresponding to the token.

    Raises:
        CustomHTTPException: If the token is invalid or the user is not found.
    """
    # Decode the token
    access_secret_key = os.environ.get("ACCESS_SECRET_KEY") or current_app.config.get("ACCESS_SECRET_KEY") if secret_key is None else secret_key

    payload = decode_token(token, access_secret_key)

    # Get user lookup field and primary key
    pk, lookup_field = get_pk_and_lookups()

    # Get the user model (this is the SQLAlchemy model)
    usr_model_class = get_config_or_model_meta("API_USER_MODEL")

    # Query the user by primary key or lookup field (like username)
    try:
        user = (
            get_session(usr_model_class)
            .query(usr_model_class)
            .filter(
                getattr(usr_model_class, lookup_field) == payload[lookup_field],
                getattr(usr_model_class, pk) == payload[pk],
            )
            .one()
        )
    except NoResultFound as exc:
        raise CustomHTTPException(status_code=404, reason="User not found") from exc

    return user
