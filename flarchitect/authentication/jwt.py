import datetime
import os

import jwt
from flask import current_app
from sqlalchemy.exc import NoResultFound

from flarchitect.database.utils import get_primary_keys
from flarchitect.exceptions import CustomHTTPException
from flarchitect.utils.config_helpers import get_config_or_model_meta

# Secret keys (keep them secure)


# In-memory store for refresh tokens (use a persistent database in production)
refresh_tokens_store = {}


def get_pk_and_lookups():
    """
    Get the primary key and lookup field for the user model.
    """
    lookup_field = get_config_or_model_meta("API_USER_LOOKUP_FIELD")
    usr = get_config_or_model_meta("API_USER_MODEL")
    primary_keys = get_primary_keys(usr)
    return primary_keys.name, lookup_field


def generate_access_token(usr_model, expires_in_minutes=360):
    """
    Generates a short-lived access token (JWT).
    """
    pk, lookup_field = get_pk_and_lookups()

    ACCESS_SECRET_KEY = os.environ.get("ACCESS_SECRET_KEY") or current_app.config.get(
        "ACCESS_SECRET_KEY"
    )

    payload = {
        lookup_field: str(getattr(usr_model, lookup_field)),  # Convert UUID to string
        pk: str(getattr(usr_model, pk)),  # Convert UUID to string
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(minutes=expires_in_minutes),
        "iat": datetime.datetime.now(datetime.timezone.utc),
    }
    token = jwt.encode(payload, ACCESS_SECRET_KEY, algorithm="HS256")
    return token


def generate_refresh_token(usr_model, expires_in_days=2):
    """
    Generates a long-lived refresh token (JWT).
    """
    REFRESH_SECRET_KEY = os.environ.get("REFRESH_SECRET_KEY") or current_app.config.get(
        "REFRESH_SECRET_KEY"
    )

    pk, lookup_field = get_pk_and_lookups()

    payload = {
        lookup_field: str(getattr(usr_model, lookup_field)),  # Convert UUID to string
        pk: str(getattr(usr_model, pk)),  # Convert UUID to string
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(days=expires_in_days),
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


def decode_token(token, secret_key):
    """
    Decodes a JWT token.
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise CustomHTTPException(status_code=401, reason="Token has expired")

    except jwt.InvalidTokenError:
        raise CustomHTTPException(status_code=401, reason="Invalid token")


def refresh_access_token(refresh_token):
    """
    Uses a refresh token to generate a new access token and returns the user.

    Args:
        refresh_token (str): The JWT refresh token.

    Returns:
        tuple: A tuple containing the new access token (str) and the user object.

    Raises:
        CustomHTTPException: If the token is invalid, expired, or the user is not found.
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
    lookup_value = stored_token.get(lookup_field)
    pk_value = stored_token.get(pk_field)

    # Get the user model (this is the SQLAlchemy model)
    usr_model_class = get_config_or_model_meta("API_USER_MODEL")

    # Query the user by lookup_field and pk
    try:
        user = (
            usr_model_class.get_session()
            .query(usr_model_class)
            .filter(
                getattr(usr_model_class, lookup_field) == lookup_value,
                getattr(usr_model_class, pk_field) == pk_value,
            )
            .one()
        )
    except NoResultFound:
        raise CustomHTTPException(status_code=404, reason="User not found")

    # Generate new access token
    new_access_token = generate_access_token(user)

    refresh_tokens_store.pop(refresh_token)

    return new_access_token, user


def get_user_from_token(token, secret_key=None):
    """
    Decodes a JWT token and returns the user associated with the token.

    Args:
        token (str): The JWT token containing user information.
        secret_key (str, optional): The secret key used to decode the token.
                                     If None, uses access secret key.

    Returns:
        usr_model: The user object.

    Raises:
        CustomHTTPException: If the token is invalid or the user is not found.
    """
    # Decode the token
    if secret_key is None:
        ACCESS_SECRET_KEY = os.environ.get(
            "ACCESS_SECRET_KEY"
        ) or current_app.config.get("ACCESS_SECRET_KEY")
    else:
        ACCESS_SECRET_KEY = secret_key

    payload = decode_token(token, ACCESS_SECRET_KEY)

    # Get user lookup field and primary key
    pk, lookup_field = get_pk_and_lookups()

    # Get the user model (this is the SQLAlchemy model)
    usr_model_class = get_config_or_model_meta("API_USER_MODEL")

    # Query the user by primary key or lookup field (like username)
    try:
        user = (
            usr_model_class.get_session()
            .query(usr_model_class)
            .filter(
                getattr(usr_model_class, lookup_field) == payload[lookup_field],
                getattr(usr_model_class, pk) == payload[pk],
            )
            .one()
        )
    except NoResultFound:
        raise CustomHTTPException(status_code=404, reason="User not found")

    return user
