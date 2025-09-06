import datetime
import os
from collections.abc import Sequence
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


def get_jwt_algorithm() -> str:
    """Retrieve the JWT signing algorithm from configuration.

    Returns:
        str: The algorithm used for encoding and decoding JWTs. Defaults to
        ``"HS256"`` when not explicitly configured.
    """

    return get_config_or_model_meta("API_JWT_ALGORITHM", default="HS256")


def get_allowed_algorithms() -> list[str]:
    """Allowed algorithms list for verification.

    Returns:
        list[str]: Algorithms permitted when decoding tokens. Defaults to the
        single configured algorithm if an explicit allow-list is not provided.
    """

    configured = get_config_or_model_meta("API_JWT_ALLOWED_ALGORITHMS", default=None)
    if configured:
        # Accept list/tuple or comma-separated string
        if isinstance(configured, list | tuple | set):
            return [str(a) for a in configured]
        return [s.strip() for s in str(configured).split(",") if s.strip()]
    return [get_jwt_algorithm()]


def _is_rs_alg(alg: str) -> bool:
    return alg.upper().startswith("RS")


def _get_access_signing_key(algorithm: str) -> str:
    if _is_rs_alg(algorithm):
        key = os.environ.get("ACCESS_PRIVATE_KEY") or current_app.config.get("ACCESS_PRIVATE_KEY")
        if key is None:
            # Fall back for compatibility in case private/public not set but single key provided
            key = os.environ.get("ACCESS_SECRET_KEY") or current_app.config.get("ACCESS_SECRET_KEY")
        if key is None:
            raise CustomHTTPException(status_code=500, reason="ACCESS_PRIVATE_KEY missing")
        return key
    # HS* symmetric
    key = os.environ.get("ACCESS_SECRET_KEY") or current_app.config.get("ACCESS_SECRET_KEY")
    if key is None:
        raise CustomHTTPException(status_code=500, reason="ACCESS_SECRET_KEY missing")
    return key


def _get_access_verifying_key(algorithm: str) -> str:
    if _is_rs_alg(algorithm):
        key = os.environ.get("ACCESS_PUBLIC_KEY") or current_app.config.get("ACCESS_PUBLIC_KEY")
        if key is None:
            # Allow fallback to ACCESS_SECRET_KEY to ease migration if a single key is provided
            key = os.environ.get("ACCESS_SECRET_KEY") or current_app.config.get("ACCESS_SECRET_KEY")
        if key is None:
            raise CustomHTTPException(status_code=500, reason="ACCESS_PUBLIC_KEY missing")
        return key
    key = os.environ.get("ACCESS_SECRET_KEY") or current_app.config.get("ACCESS_SECRET_KEY")
    if key is None:
        raise CustomHTTPException(status_code=500, reason="ACCESS_SECRET_KEY missing")
    return key


def _get_refresh_signing_key(algorithm: str) -> str:
    if _is_rs_alg(algorithm):
        key = os.environ.get("REFRESH_PRIVATE_KEY") or current_app.config.get("REFRESH_PRIVATE_KEY")
        if key is None:
            key = os.environ.get("REFRESH_SECRET_KEY") or current_app.config.get("REFRESH_SECRET_KEY")
        if key is None:
            raise CustomHTTPException(status_code=500, reason="REFRESH_PRIVATE_KEY missing")
        return key
    key = os.environ.get("REFRESH_SECRET_KEY") or current_app.config.get("REFRESH_SECRET_KEY")
    if key is None:
        raise CustomHTTPException(status_code=500, reason="REFRESH_SECRET_KEY missing")
    return key


def _get_refresh_verifying_key(algorithm: str) -> str:
    if _is_rs_alg(algorithm):
        key = os.environ.get("REFRESH_PUBLIC_KEY") or current_app.config.get("REFRESH_PUBLIC_KEY")
        if key is None:
            key = os.environ.get("REFRESH_SECRET_KEY") or current_app.config.get("REFRESH_SECRET_KEY")
        if key is None:
            raise CustomHTTPException(status_code=500, reason="REFRESH_PUBLIC_KEY missing")
        return key
    key = os.environ.get("REFRESH_SECRET_KEY") or current_app.config.get("REFRESH_SECRET_KEY")
    if key is None:
        raise CustomHTTPException(status_code=500, reason="REFRESH_SECRET_KEY missing")
    return key


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
    # Optional claims from config
    issuer = get_config_or_model_meta("API_JWT_ISSUER", default=None)
    audience = get_config_or_model_meta("API_JWT_AUDIENCE", default=None)
    payload = {
        **payload,
        "exp": now + datetime.timedelta(minutes=exp_minutes),
        "iat": now,
    }
    if issuer:
        payload["iss"] = issuer
    if audience:
        payload["aud"] = audience
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
    exp_minutes = expires_in_minutes or get_config_or_model_meta("API_JWT_EXPIRY_TIME", default=360)

    algorithm = get_jwt_algorithm()
    ACCESS_SECRET_KEY = _get_access_signing_key(algorithm)

    payload = {
        lookup_field: str(getattr(usr_model, lookup_field)),  # Convert UUID to string
        pk: str(getattr(usr_model, pk)),  # Convert UUID to string
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=exp_minutes),
        "iat": datetime.datetime.now(datetime.timezone.utc),
    }
    token, _ = create_jwt(payload, ACCESS_SECRET_KEY, exp_minutes, algorithm)
    return token


def generate_refresh_token(usr_model: Any, expires_in_minutes: int | None = None) -> str:
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

    pk, lookup_field = get_pk_and_lookups()
    exp_minutes = expires_in_minutes or get_config_or_model_meta("API_JWT_REFRESH_EXPIRY_TIME", default=2880)

    payload = {
        lookup_field: str(getattr(usr_model, lookup_field)),  # Convert UUID to string
        pk: str(getattr(usr_model, pk)),  # Convert UUID to string
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=exp_minutes),
        "iat": datetime.datetime.now(datetime.timezone.utc),
    }

    algorithm = get_jwt_algorithm()
    REFRESH_SECRET_KEY = _get_refresh_signing_key(algorithm)
    token, payload = create_jwt(payload, REFRESH_SECRET_KEY, exp_minutes, algorithm)

    store_refresh_token(
        token=token,
        user_pk=payload[pk],
        user_lookup=payload[lookup_field],
        expires_at=payload["exp"],
    )

    return token


def decode_token(
    token: str,
    secret_key: str,
    algorithm: str | None = None,
    *,
    allowed_algorithms: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Decode a JWT and return its payload.

    Args:
        token: The encoded JWT.
        secret_key: The secret key used to decode the token.
        algorithm: Optional JWT algorithm hint. When not provided, uses the
            configured algorithm.
        allowed_algorithms: Optional explicit list of allowed algorithms for
            verification. Defaults to configured allow-list.

    Returns:
        dict[str, Any]: The decoded token payload.

    Raises:
        CustomHTTPException: If the token is expired or invalid.
    """

    algorithm = algorithm or get_jwt_algorithm()
    allowed = list(allowed_algorithms or get_allowed_algorithms())
    # Leeway and validation params
    leeway = get_config_or_model_meta("API_JWT_LEEWAY", default=0)
    issuer = get_config_or_model_meta("API_JWT_ISSUER", default=None)
    audience = get_config_or_model_meta("API_JWT_AUDIENCE", default=None)

    # Normalise common token formats (e.g., "Bearer <token>")
    if isinstance(token, str) and token.lower().startswith("bearer "):
        token = token.split(" ", 1)[1].strip()

    # Basic structural validation to avoid PyJWT low-level errors
    if not isinstance(token, str) or token.count(".") < 2:
        # Keep message generic to avoid leaking details
        raise CustomHTTPException(status_code=401, reason="Invalid token")

    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=allowed,
            leeway=leeway,
            issuer=issuer if issuer else None,
            audience=audience if audience else None,
        )
        return payload
    except jwt.ExpiredSignatureError as exc:
        raise CustomHTTPException(status_code=401, reason="Token has expired") from exc
    except jwt.InvalidIssuerError as exc:
        raise CustomHTTPException(status_code=401, reason="Invalid token") from exc
    except jwt.InvalidAudienceError as exc:
        raise CustomHTTPException(status_code=401, reason="Invalid token") from exc
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
        CustomHTTPException: If ``REFRESH_SECRET_KEY`` is missing, the token is
        invalid or expired, or the user cannot be found.
    """
    # Verify refresh token
    algorithm = get_jwt_algorithm()
    REFRESH_SECRET_KEY = _get_refresh_verifying_key(algorithm)

    try:
        decode_token(refresh_token, REFRESH_SECRET_KEY)
    except CustomHTTPException as exc:
        if exc.reason == "Token has expired":
            # Expired tokens are invalid; keep row for audit but ensure not usable
            try:
                from flarchitect.authentication.token_store import revoke_refresh_token

                revoke_refresh_token(refresh_token)
            except Exception:
                # Best-effort; if token store is unavailable, proceed with error
                pass
        raise

    stored_token = get_refresh_token(refresh_token)
    if stored_token is None:
        raise CustomHTTPException(status_code=403, reason="Invalid or expired refresh token")

    expires_at = stored_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=datetime.timezone.utc)
    if datetime.datetime.now(datetime.timezone.utc) > expires_at:
        delete_refresh_token(refresh_token)
        raise CustomHTTPException(status_code=403, reason="Invalid or expired refresh token")

    # Get user identifiers from stored_token
    pk_field, lookup_field = get_pk_and_lookups()
    lookup_value = stored_token.user_lookup
    pk_value = stored_token.user_pk

    # Get the user model (this is the SQLAlchemy model)
    usr_model_class = get_config_or_model_meta("API_USER_MODEL")

    # Query the user by lookup_field and pk
    try:
        with get_session(usr_model_class) as session:
            user = (
                session.query(usr_model_class)
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

    # Mark the refresh token as used and revoked (single-use semantics)
    try:
        from flarchitect.authentication.token_store import mark_refresh_token_used, revoke_refresh_token

        mark_refresh_token_used(refresh_token)
        revoke_refresh_token(refresh_token)
    except Exception:
        # Best-effort auditing; do not block token refresh on audit storage
        pass

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
        CustomHTTPException: If ``ACCESS_SECRET_KEY`` is missing, the token is
        invalid, or the user is not found.
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
    if access_secret_key is None:
        # If using RS*, fall back to public key config
        alg = get_jwt_algorithm()
        if _is_rs_alg(alg):
            access_secret_key = os.environ.get("ACCESS_PUBLIC_KEY") or current_app.config.get("ACCESS_PUBLIC_KEY")
    if access_secret_key is None:
        raise CustomHTTPException(status_code=500, reason="ACCESS_SECRET_KEY missing")

    payload = decode_token(token, access_secret_key)

    # Get user lookup field and primary key
    pk, lookup_field = get_pk_and_lookups()

    # Get the user model (this is the SQLAlchemy model)
    usr_model_class = get_config_or_model_meta("API_USER_MODEL")

    # Query the user by primary key or lookup field (like username)
    try:
        with get_session(usr_model_class) as session:
            user = (
                session.query(usr_model_class)
                .filter(
                    getattr(usr_model_class, lookup_field) == payload[lookup_field],
                    getattr(usr_model_class, pk) == payload[pk],
                )
                .one()
            )
    except NoResultFound as exc:
        raise CustomHTTPException(status_code=404, reason="User not found") from exc

    return user
