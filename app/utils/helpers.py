"""Utility helpers — ID generation, timestamps, pagination, Cypher builders."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone


def generate_id() -> str:
    """Generate a unique ID string."""
    return str(uuid.uuid4())


def utc_now() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today_str() -> str:
    """Return today's date as YYYY-MM-DD."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def build_set_clause(data: dict, node_var: str = "n") -> tuple[str, dict]:
    """Build a Cypher SET clause from a dict of {field: value}.

    Returns (set_clause_str, params_dict).
    Skips None values.
    """
    parts: list[str] = []
    params: dict = {}
    for key, value in data.items():
        if value is not None:
            param_name = f"upd_{key}"
            parts.append(f"{node_var}.{key} = ${param_name}")
            params[param_name] = value
    # Always update updated_at
    parts.append(f"{node_var}.updated_at = $upd_updated_at")
    params["upd_updated_at"] = utc_now()

    return ", ".join(parts), params


def build_filter_clause(
    filters: dict,
    node_var: str = "n",
    prefix: str = "flt",
) -> tuple[str, dict]:
    """Build a Cypher WHERE clause from a dict of {field: value}.

    Returns (where_conditions_str, params_dict).
    Skips None and empty-string values.
    """
    conditions: list[str] = []
    params: dict = {}
    for key, value in filters.items():
        if value is not None and value != "":
            param_name = f"{prefix}_{key}"
            conditions.append(f"{node_var}.{key} = ${param_name}")
            params[param_name] = value
    return " AND ".join(conditions) if conditions else "", params


def build_search_clause(
    search: str,
    fields: list[str],
    node_var: str = "n",
) -> tuple[str, dict]:
    """Build a case-insensitive CONTAINS search across multiple fields.

    Returns (search_clause_str, params_dict).
    """
    if not search or not fields:
        return "", {}
    conditions = [
        f"toLower({node_var}.{field}) CONTAINS toLower($search_term)"
        for field in fields
    ]
    return f"({' OR '.join(conditions)})", {"search_term": search}


def build_order_clause(
    sort_by: str = "created_at",
    sort_order: str = "desc",
    node_var: str = "n",
) -> str:
    """Build a Cypher ORDER BY clause."""
    direction = "DESC" if sort_order.lower() == "desc" else "ASC"
    return f"ORDER BY {node_var}.{sort_by} {direction}"


def node_to_dict(node: object) -> dict:
    """Convert a Neo4j Node (or Record value) to a plain dict."""
    if hasattr(node, "items"):
        return dict(node.items())
    if isinstance(node, dict):
        return node
    return dict(node)
