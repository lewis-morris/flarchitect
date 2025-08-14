import datetime
import os
from typing import Any

import jwt
from flask import current_app
from sqlalchemy.exc import NoResultFound

from flarchitect.authentication.token_store import (
    delete_refresh_token,
    get_refresh_token,
    store_refresh_token,
)
from flarchitect.database.utils import get_primary_keys
from flarchitect.exceptions import CustomHTTPException
from flarchitect.utils.config_helpers import get_config_or_model_meta
from flarchitect.utils.session import get_session

# Secret keys (keep them secure)


# In-memory store for refresh tokens (use a persistent database in production)
refresh_tokens_store: dict[str, dict[str, Any]] = {}


def get_jwt_algorithm() -> str:
    """Retrieve the JWT signing algorithm from configuration.

    Returns:
        str: The algorithm used for encoding and decoding JWTs. Defaults to
        ``"HS256"`` when not explicitly configured.
    """

    return get_config_or_model_meta("API_JWT_ALGORITHM", default="HS256")


def create_jwt(
    payload: dict[str, Any],
    secret_key: str,
    exp_minutes: int,
    algorithm: str,
) -> tuple[str, dict[str, Any]]:
    """Generate a JSON Web Token and return the token and payload.

    Args:
        payload: Base payload without temporal claims.
        secret_key: Key used to sign the token.
        exp_minutes: Number of minutes until the token expires.
        algorithm: JWT signing algorithm.

    Returns:
        tuple[str, dict[str, Any]]: The encoded token and payload including
        ``exp`` and ``iat`` claims.
    """

    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        **payload,
        "exp": now + datetime.timedelta(minutes=exp_minutes),
        "iat": now,
    }
    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    return token, payload

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


def generate_access_token(usr_model: Any, expires_in_minutes: int | None = None) -> str:
    """Create a short-lived JSON Web Token for ``usr_model``.

    The expiry time defaults to the value of ``API_JWT_EXPIRY_TIME`` if present
    on the Flask config. When unset, tokens last ``360`` minutes (six hours).

    Args:
        usr_model: The user model instance for which to create the token.
        expires_in_minutes: Optional override for the token lifetime in minutes.

    Returns:
        The encoded JWT access token.

    Raises:
        CustomHTTPException: If the access secret key is not configured.
    """

    pk, lookup_field = get_pk_and_lookups()
    exp_minutes = expires_in_minutes or get_config_or_model_meta(
        "API_JWT_EXPIRY_TIME", default=360
    )

    ACCESS_SECRET_KEY = os.environ.get("ACCESS_SECRET_KEY") or current_app.config.get(
        "ACCESS_SECRET_KEY"
    )
    if ACCESS_SECRET_KEY is None:
        raise CustomHTTPException(status_code=500, reason="ACCESS_SECRET_KEY missing")

    algorithm = get_jwt_algorithm()

    payload = {
        lookup_field: str(getattr(usr_model, lookup_field)),
        pk: str(getattr(usr_model, pk)),
    }
    token, _ = create_jwt(payload, ACCESS_SECRET_KEY, exp_minutes, algorithm)
    return token


def generate_refresh_token(
    usr_model: Any, expires_in_minutes: int | None = None
) -> str:
    """Create a long-lived refresh token for ``usr_model``.

    The expiry time defaults to ``API_JWT_REFRESH_EXPIRY_TIME`` from the Flask
    config. When unset, refresh tokens last ``2880`` minutes (two days).

    Args:
        usr_model: The user model instance for which to create the token.
        expires_in_minutes: Optional override for the token lifetime in minutes.

    Returns:
        The encoded JWT refresh token.

    Raises:
        CustomHTTPException: If the refresh secret key is not configured.
    """

    REFRESH_SECRET_KEY = os.environ.get("REFRESH_SECRET_KEY") or current_app.config.get(
        "REFRESH_SECRET_KEY"
    )
    if REFRESH_SECRET_KEY is None:
        raise CustomHTTPException(status_code=500, reason="REFRESH_SECRET_KEY missing")

    pk, lookup_field = get_pk_and_lookups()
    exp_minutes = expires_in_minutes or get_config_or_model_meta(
        "API_JWT_REFRESH_EXPIRY_TIME", default=2880
    )

    algorithm = get_jwt_algorithm()

    payload = {
        lookup_field: str(getattr(usr_model, lookup_field)),
        pk: str(getattr(usr_model, pk)),
    }
    token, payload = create_jwt(payload, REFRESH_SECRET_KEY, exp_minutes, algorithm)

    refresh_tokens_store[token] = {
        lookup_field: payload[lookup_field],
        pk: payload[pk],
        "expires_at": payload["exp"],
    }

    return token


def decode_token(
    token: str, secret_key: str, algorithm: str | None = None
) -> dict[str, Any]:
    """Decode a JWT and return its payload.

    Args:
        token: The encoded JWT.
        secret_key: The secret key used to decode the token.
        algorithm: Optional JWT algorithm to use for decoding. Defaults to the
            configured algorithm.

    Returns:
        dict[str, Any]: The decoded token payload.

    Raises:
        CustomHTTPException: If the token is expired or invalid.
    """

    algorithm = algorithm or get_jwt_algorithm()

    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
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
    REFRESH_SECRET_KEY = os.environ.get("REFRESH_SECRET_KEY") or current_app.config.get(
        "REFRESH_SECRET_KEY"
    )
    payload = decode_token(refresh_token, REFRESH_SECRET_KEY)
    if payload is None:
        raise CustomHTTPException(status_code=401, reason="Invalid token")

    # Check if the refresh token is in the store and not expired
    stored_token = refresh_tokens_store.get(refresh_token)
    if (
        not stored_token
        or datetime.datetime.now(datetime.timezone.utc) > stored_token["expires_at"]

    ):
        raise CustomHTTPException(
            status_code=403, reason="Invalid or expired refresh token"
        )

    # Get user identifiers from stored_token
    pk_field, lookup_field = get_pk_and_lookups()
    lookup_value = stored_token.user_lookup
    pk_value = stored_token.user_pk

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

    delete_refresh_token(refresh_token)

    return new_access_token, user


def get_user_from_token(token: str, secret_key: str | None = None) -> Any:
    """Decode a token and return the associated user.

    Args:
        token (str): The JWT containing user information.
        secret_key (str | None, optional): The secret key used to decode the
            token. If ``None``, falls back to the ``ACCESS_SECRET_KEY``
            environment variable, then ``current_app.config['ACCESS_SECRET_KEY']``.

    Returns:
        Any: The user model instance corresponding to the token.

    Raises:
        CustomHTTPException: If the token is invalid or the user is not found.
    """
    # Determine secret key priority:
    # 1. Explicit ``secret_key`` argument
    # 2. ``ACCESS_SECRET_KEY`` environment variable
    # 3. ``current_app.config['ACCESS_SECRET_KEY']``
    # fmt: off
    access_secret_key = (
        secret_key
        or os.environ.get("ACCESS_SECRET_KEY")
        or current_app.config.get("ACCESS_SECRET_KEY")
    )
    # fmt: on

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
