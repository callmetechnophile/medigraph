"""Base repository — shared CRUD patterns for all Neo4j node repositories."""

from __future__ import annotations

from typing import Any

import structlog
from neo4j import AsyncDriver

from app.utils.helpers import (
    build_filter_clause,
    build_order_clause,
    build_search_clause,
    build_set_clause,
    generate_id,
    node_to_dict,
    utc_now,
)

logger = structlog.get_logger(__name__)


class BaseRepository:
    """Abstract base repository providing common CRUD operations.

    Subclasses must set ``label`` (the Neo4j node label) and may override
    ``search_fields`` for text-search support.
    """

    label: str = ""
    search_fields: list[str] = ["name"]

    def __init__(self, driver: AsyncDriver, database: str = "neo4j"):
        self.driver = driver
        self.database = database

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------
    async def create(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new node and return it as a dict."""
        data.setdefault("id", generate_id())
        data.setdefault("created_at", utc_now())
        data.setdefault("updated_at", utc_now())

        # Build property assignment string
        props = ", ".join(f"{k}: ${k}" for k in data)
        query = f"CREATE (n:{self.label} {{{props}}}) RETURN n"

        records, _, _ = await self.driver.execute_query(
            query, **data, database_=self.database
        )
        logger.info(f"{self.label}.created", id=data["id"])
        return node_to_dict(records[0]["n"]) if records else data

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------
    async def find_by_id(self, entity_id: str) -> dict[str, Any] | None:
        """Find a single node by its ``id`` property."""
        query = f"MATCH (n:{self.label} {{id: $id}}) RETURN n"
        records, _, _ = await self.driver.execute_query(
            query, id=entity_id, database_=self.database
        )
        return node_to_dict(records[0]["n"]) if records else None

    async def find_all(
        self,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        search: str = "",
        filters: dict[str, Any] | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """Return a paginated list of nodes and the total count.

        Returns:
            (items, total_count)
        """
        where_parts: list[str] = []
        params: dict[str, Any] = {}

        # Filters
        if filters:
            clause, fparams = build_filter_clause(filters)
            if clause:
                where_parts.append(clause)
                params.update(fparams)

        # Search
        if search and self.search_fields:
            clause, sparams = build_search_clause(search, self.search_fields)
            if clause:
                where_parts.append(clause)
                params.update(sparams)

        where_str = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
        order_str = build_order_clause(sort_by, sort_order)

        # Count query
        count_query = f"MATCH (n:{self.label}) {where_str} RETURN count(n) AS total"
        count_records, _, _ = await self.driver.execute_query(
            count_query, **params, database_=self.database
        )
        total = count_records[0]["total"] if count_records else 0

        # Data query
        data_query = (
            f"MATCH (n:{self.label}) {where_str} "
            f"RETURN n {order_str} SKIP $skip LIMIT $limit"
        )
        params["skip"] = skip
        params["limit"] = limit

        records, _, _ = await self.driver.execute_query(
            data_query, **params, database_=self.database
        )
        items = [node_to_dict(r["n"]) for r in records]
        return items, total

    async def exists(self, entity_id: str) -> bool:
        """Check whether a node with the given ID exists."""
        query = f"MATCH (n:{self.label} {{id: $id}}) RETURN count(n) AS cnt"
        records, _, _ = await self.driver.execute_query(
            query, id=entity_id, database_=self.database
        )
        return records[0]["cnt"] > 0 if records else False

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------
    async def update(
        self, entity_id: str, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Update a node's properties and return the updated node."""
        # Remove None values and build SET clause
        clean_data = {k: v for k, v in data.items() if v is not None}
        if not clean_data:
            return await self.find_by_id(entity_id)

        set_clause, set_params = build_set_clause(clean_data)
        query = (
            f"MATCH (n:{self.label} {{id: $id}}) "
            f"SET {set_clause} "
            f"RETURN n"
        )
        set_params["id"] = entity_id

        records, _, _ = await self.driver.execute_query(
            query, **set_params, database_=self.database
        )
        if records:
            logger.info(f"{self.label}.updated", id=entity_id)
            return node_to_dict(records[0]["n"])
        return None

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------
    async def delete(self, entity_id: str) -> bool:
        """Delete a node and all its relationships."""
        query = f"MATCH (n:{self.label} {{id: $id}}) DETACH DELETE n RETURN count(*) AS cnt"
        records, _, _ = await self.driver.execute_query(
            query, id=entity_id, database_=self.database
        )
        deleted = records[0]["cnt"] > 0 if records else False
        if deleted:
            logger.info(f"{self.label}.deleted", id=entity_id)
        return deleted

    # ------------------------------------------------------------------
    # Relationship helpers
    # ------------------------------------------------------------------
    async def create_relationship(
        self,
        from_label: str,
        from_id: str,
        rel_type: str,
        to_label: str,
        to_id: str,
        properties: dict[str, Any] | None = None,
    ) -> bool:
        """Create a relationship between two nodes."""
        props_str = ""
        params: dict[str, Any] = {"from_id": from_id, "to_id": to_id}
        if properties:
            prop_parts = ", ".join(f"{k}: $rel_{k}" for k in properties)
            props_str = f" {{{prop_parts}}}"
            params.update({f"rel_{k}": v for k, v in properties.items()})

        query = (
            f"MATCH (a:{from_label} {{id: $from_id}}), (b:{to_label} {{id: $to_id}}) "
            f"MERGE (a)-[r:{rel_type}{props_str}]->(b) "
            f"RETURN type(r) AS rel"
        )
        records, _, _ = await self.driver.execute_query(
            query, **params, database_=self.database
        )
        return bool(records)

    async def delete_relationship(
        self,
        from_label: str,
        from_id: str,
        rel_type: str,
        to_label: str,
        to_id: str,
    ) -> bool:
        """Delete a specific relationship between two nodes."""
        query = (
            f"MATCH (a:{from_label} {{id: $from_id}})"
            f"-[r:{rel_type}]->"
            f"(b:{to_label} {{id: $to_id}}) "
            f"DELETE r RETURN count(*) AS cnt"
        )
        records, _, _ = await self.driver.execute_query(
            query, from_id=from_id, to_id=to_id, database_=self.database
        )
        return records[0]["cnt"] > 0 if records else False

    async def get_related_nodes(
        self,
        from_id: str,
        rel_type: str,
        target_label: str,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        """Get nodes related to this entity via a specific relationship."""
        count_query = (
            f"MATCH (a:{self.label} {{id: $from_id}})-[:{rel_type}]->(b:{target_label}) "
            f"RETURN count(b) AS total"
        )
        count_records, _, _ = await self.driver.execute_query(
            count_query, from_id=from_id, database_=self.database
        )
        total = count_records[0]["total"] if count_records else 0

        data_query = (
            f"MATCH (a:{self.label} {{id: $from_id}})-[:{rel_type}]->(b:{target_label}) "
            f"RETURN b ORDER BY b.created_at DESC SKIP $skip LIMIT $limit"
        )
        records, _, _ = await self.driver.execute_query(
            data_query,
            from_id=from_id,
            skip=skip,
            limit=limit,
            database_=self.database,
        )
        items = [node_to_dict(r["b"]) for r in records]
        return items, total
