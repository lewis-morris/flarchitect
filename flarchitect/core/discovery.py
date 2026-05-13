"""Runtime schema discovery helpers."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import RelationshipProperty

from flarchitect.database.utils import AGGREGATE_FUNCS, OPERATORS, normalise_join_token
from flarchitect.utils.config_helpers import get_config_or_model_meta


def build_schema_discovery_payload(
    *,
    models: Iterable[type],
    created_routes: dict[str, dict[str, Any]] | None = None,
    model_filter: set[str] | None = None,
    max_depth: int = 2,
) -> dict[str, Any]:
    """Assemble schema discovery details for the provided models.

    Args:
        models: Iterable of SQLAlchemy declarative models to describe.
        created_routes: Optional mapping of registered routes for endpoint metadata.
        model_filter: Optional set of lowercase tokens to restrict the models returned.
        max_depth: Maximum relationship depth for join path enumeration.

    Returns:
        dict[str, Any]: Discovery payload describing models, filters, operators, and joins.
    """

    if max_depth < 1:
        max_depth = 1

    endpoints_by_model: dict[type, list[dict[str, Any]]] = defaultdict(list)
    if created_routes:
        for info in created_routes.values():
            model = info.get("model")
            if model is None:
                continue
            endpoints_by_model[model].append({
                "method": info.get("method"),
                "url": info.get("url"),
            })

    payload_models: list[dict[str, Any]] = []

    for model in sorted({m for m in models if hasattr(m, "__table__")}, key=lambda x: x.__name__):
        if model_filter and not _matches_model_filter(model, endpoints_by_model.get(model, []), model_filter):
            continue
        payload_models.append(
            _describe_model(
                model=model,
                endpoints=endpoints_by_model.get(model, []),
                max_depth=max_depth,
            )
        )

    return {
        "operators": sorted(OPERATORS.keys()),
        "aggregates": sorted(AGGREGATE_FUNCS.keys()),
        "models": payload_models,
    }


def _matches_model_filter(
    model: type,
    endpoints: list[dict[str, Any]],
    tokens: set[str],
) -> bool:
    """Return True if the model matches any filter token."""

    if not tokens:
        return True

    candidates = {
        model.__name__.lower(),
        getattr(model, "__tablename__", "").lower(),
    }
    for endpoint in endpoints:
        url = str(endpoint.get("url", "")).strip().lower()
        if url:
            candidates.add(url)
            candidates.update(segment for segment in url.strip("/").split("/") if segment)
    return any(token in candidates for token in tokens)


def _describe_model(
    *,
    model: type,
    endpoints: list[dict[str, Any]],
    max_depth: int,
) -> dict[str, Any]:
    """Return discovery metadata for a single model."""

    inspector = sa_inspect(model)
    primary_keys = [col.key for col in inspector.primary_key]
    table_name = getattr(model, "__tablename__", None)
    field_case = get_config_or_model_meta("API_FIELD_CASE", model=model, default="snake") or "snake"
    allow_filters = bool(get_config_or_model_meta("API_ALLOW_FILTERS", model=model, default=True))
    allow_order = bool(get_config_or_model_meta("API_ALLOW_ORDER_BY", model=model, default=True))
    allow_group = bool(get_config_or_model_meta("API_ALLOW_GROUPBY", model=model, default=False))
    allow_agg = bool(get_config_or_model_meta("API_ALLOW_AGGREGATION", model=model, default=False))

    fields = _collect_fields(model=model, allow_filters=allow_filters)
    relationships = _collect_relationships(model=model)
    join_paths = _collect_join_paths(model=model, max_depth=max_depth)

    return {
        "name": model.__name__,
        "table": table_name,
        "primary_key": primary_keys,
        "field_case": field_case,
        "filters_enabled": allow_filters,
        "ordering_enabled": allow_order,
        "grouping_enabled": allow_group,
        "aggregation_enabled": allow_agg,
        "fields": fields,
        "relationships": relationships,
        "join_paths": join_paths,
        "endpoints": _deduplicate_endpoints(endpoints),
    }


def _collect_fields(*, model: type, allow_filters: bool) -> list[dict[str, Any]]:
    inspector = sa_inspect(model)
    fields: list[dict[str, Any]] = []

    for column in inspector.columns:
        fields.append(
            {
                "name": column.key,
                "type": type(column.type).__name__,
                "nullable": bool(column.nullable),
                "primary_key": bool(column.primary_key),
                "filterable": allow_filters,
                "operators": sorted(OPERATORS.keys()) if allow_filters else [],
                "source": "column",
            }
        )

    # Include hybrid properties for reference
    for name, attr in vars(model).items():
        if isinstance(attr, hybrid_property):
            fields.append(
                {
                    "name": name,
                    "type": "hybrid_property",
                    "nullable": True,
                    "primary_key": False,
                    "filterable": allow_filters,
                    "operators": sorted(OPERATORS.keys()) if allow_filters else [],
                    "source": "hybrid",
                }
            )

    return sorted(fields, key=lambda item: item["name"])


def _collect_relationships(*, model: type) -> list[dict[str, Any]]:
    inspector = sa_inspect(model)
    relationships: list[dict[str, Any]] = []

    for rel in inspector.relationships:  # type: RelationshipProperty
        relationships.append(
            {
                "name": rel.key,
                "join_token": normalise_join_token(rel.key),
                "target": rel.mapper.class_.__name__,
                "direction": rel.direction.name.lower(),
                "uselist": bool(rel.uselist),
                "back_populates": rel.back_populates or getattr(rel.backref, "key", None) if rel.backref else None,
            }
        )

    return sorted(relationships, key=lambda item: item["name"])


def _collect_join_paths(*, model: type, max_depth: int) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []

    def _walk(current: type, prefix_tokens: tuple[str, ...], seen: frozenset[type], depth: int) -> None:
        if depth <= 0:
            return
        inspector = sa_inspect(current)
        for rel in inspector.relationships:
            token = normalise_join_token(rel.key)
            if not token:
                continue
            new_tokens = prefix_tokens + (token,)
            result.append(
                {
                    "path": ".".join(new_tokens),
                    "segments": list(new_tokens),
                    "target": rel.mapper.class_.__name__,
                    "depth": len(new_tokens),
                }
            )
            related = rel.mapper.class_
            if related not in seen:
                _walk(related, new_tokens, seen | {related}, depth - 1)

    _walk(model, tuple(), frozenset({model}), max_depth)

    # Sort by depth then alphabetical path for stability
    return sorted(result, key=lambda item: (item["depth"], item["path"]))


def _deduplicate_endpoints(endpoints: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, Any]] = []
    for entry in endpoints:
        method = (entry.get("method") or "").upper()
        url = entry.get("url") or ""
        key = (method, url)
        if key in seen:
            continue
        seen.add(key)
        unique.append({"method": method, "url": url})
    return sorted(unique, key=lambda item: (item["url"], item["method"]))
