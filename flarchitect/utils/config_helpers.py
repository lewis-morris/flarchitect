from typing import Any

from flask import current_app, g, has_app_context, has_request_context, request
from marshmallow import Schema
from sqlalchemy.orm import DeclarativeBase


def _normalise_config_key(key: str) -> str:
    return key.lower()


def _method_based_keys(base_key: str, method: str) -> list[str]:
    methods = ["get", "post", "put", "patch", "delete"]
    method_name = method.lower() if isinstance(method, str) else str(method).lower()
    base_key_lower = base_key.lower()
    return [f"{candidate}_{base_key_lower}" for candidate in methods if method_name == candidate]


def _unique_keys(keys: list[str]) -> list[str]:
    return list(dict.fromkeys(keys))


def _source_lookup(
    sources: list[Any],
    keys: list[str],
    *,
    allow_join: bool,
) -> Any | None:
    joined: list[Any] = []
    for source in sources:
        meta = getattr(source, "Meta", None) if source is not None else None
        if meta is None:
            continue

        for key in keys:
            result = getattr(meta, key, None)
            if isinstance(result, list) and allow_join:
                joined.extend(result)
                continue
            if result is not None:
                return result
    return joined if allow_join else None


def _flask_config_lookup(keys: list[str]) -> Any | None:
    if not has_app_context():
        return None

    for key in keys:
        upper_key = key.upper()
        prefixed_key = f"API_{upper_key}"
        if upper_key in current_app.config:
            return current_app.config[upper_key]
        if prefixed_key in current_app.config:
            return current_app.config[prefixed_key]
    return None


def _request_cache_get(cache_key: tuple[Any, ...]) -> tuple[bool, Any]:
    if not has_request_context():
        return False, None
    cache = getattr(g, "_flarch_cfg_cache", None)
    if cache is None:
        cache = {}
        g._flarch_cfg_cache = cache
    return (True, cache[cache_key]) if cache_key in cache else (False, None)


def _request_cache_set(cache_key: tuple[Any, ...], value: Any) -> None:
    if has_request_context():
        g._flarch_cfg_cache[cache_key] = value


def _with_source(value: Any, source: str, return_from_config: bool) -> Any:
    return (value, source) if return_from_config else value


def _has_config_value(value: Any) -> bool:
    return value is not None and value != [] and value != {}


def get_config_or_model_meta(
    key: str,
    model: DeclarativeBase | None = None,
    output_schema: Schema | None = None,
    input_schema: Schema | None = None,
    default: Any = None,
    allow_join: bool = False,
    method: str = "IGNORE",
    return_from_config: bool = False,
) -> Any:
    """
    Retrieves configuration or model metadata, prioritizing model metadata.

    Args:
        key (str): The key to search for in the configuration or model meta.
        model (Optional[DeclarativeBase], optional): The SQLAlchemy model.
        output_schema (Optional[Schema], optional): The Marshmallow schema for output.
        input_schema (Optional[Schema], optional): The Marshmallow schema for input.
        default (Any, optional): The default value to return if the key is not found.
        allow_join (bool, optional): Whether to allow joining of results if multiple found.
        method (str, optional): The HTTP method (e.g., 'get', 'post').
        return_from_config (bool, optional): Whether to return the object name from which the value was retrieved.

    Returns:
        Any: The value from the config or model meta, or the default value.
    """

    normalized_key = _normalise_config_key(key)
    method_based_keys = _method_based_keys(normalized_key.replace("api_", ""), method)

    sources = [model, output_schema, input_schema]
    keys_for_sources = _unique_keys(
        [
            *method_based_keys,
            normalized_key,
            _normalise_config_key(key).replace("api_", ""),
        ]
    )
    keys_for_config = [*method_based_keys, normalized_key]

    # Request-local memoization cache (only caches positive lookups)
    cache_key: tuple = (
        normalized_key,
        getattr(model, "__name__", None) if model is not None else None,
        getattr(type(output_schema), "__name__", None) if output_schema is not None else None,
        getattr(type(input_schema), "__name__", None) if input_schema is not None else None,
        bool(allow_join),
        method.lower() if isinstance(method, str) else str(method),
        bool(return_from_config),
    )

    found, cached_value = _request_cache_get(cache_key)
    if found:
        return cached_value

    # Perform lookups
    model_result = _source_lookup(sources, keys_for_sources, allow_join=allow_join)
    if _has_config_value(model_result):
        out = _with_source(model_result, "model", return_from_config)
        _request_cache_set(cache_key, out)
        return out

    cfg_result = _flask_config_lookup(keys_for_config)
    if _has_config_value(cfg_result):
        out = _with_source(cfg_result, "config", return_from_config)
        _request_cache_set(cache_key, out)
        return out

    return _with_source(default, "default", return_from_config)


def is_xml() -> bool:
    """Check if the request is for XML data.

    Returns:
        bool: True if the request is for XML, otherwise False.
    """
    accept_header = request.headers.get("Accept", "")
    content_type_header = request.headers.get("Content-Type", "")
    return any(header in ["application/xml", "text/xml"] for header in [accept_header, content_type_header])
