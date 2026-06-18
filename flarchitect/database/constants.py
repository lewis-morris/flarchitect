"""Shared database query constants.

Keeping these small constants separate avoids import cycles between query
helpers and OpenAPI/documentation helpers.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sqlalchemy import func

OPERATORS: dict[str, Callable[[Any, Any], Any]] = {
    "lt": lambda f, a: f < a,
    "le": lambda f, a: f <= a,
    "gt": lambda f, a: f > a,
    "eq": lambda f, a: f == a,
    "neq": lambda f, a: f != a,
    "ge": lambda f, a: f >= a,
    "ne": lambda f, a: f != a,
    "in": lambda f, a: f.in_(a),
    "nin": lambda f, a: ~f.in_(a),
    "like": lambda f, a: f.like(a),
    "ilike": lambda f, a: f.ilike(a),
}

AGGREGATE_FUNCS = {
    "sum": func.sum,
    "count": func.count,
    "avg": func.avg,
    "min": func.min,
    "max": func.max,
}

OTHER_FUNCTIONS = ["groupby", "fields", "join", "orderby"]
