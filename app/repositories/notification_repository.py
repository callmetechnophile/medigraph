"""Notification repository — CRUD and status tracking for in-app Notifications."""

from __future__ import annotations

from typing import Any

from app.repositories.base_repository import BaseRepository
from app.utils.helpers import generate_id, utc_now, node_to_dict

class NotificationRepository(BaseRepository):
    label = "Notification"
    search_fields = ["title", "message"]

    async def get_by_recipient(self, recipient_id: str, skip: int = 0, limit: int = 20, is_read: bool | None = None, priority: str = "") -> tuple[list[dict[str, Any]], int]:
        where_parts = ["n.recipient_id = $recipient_id"]
        params: dict[str, Any] = {"recipient_id": recipient_id, "skip": skip, "limit": limit}

        if is_read is not None:
            where_parts.append("n.is_read = $is_read")
            params["is_read"] = is_read

        if priority:
            where_parts.append("n.priority = $priority")
            params["priority"] = priority

        where_clause = f"WHERE {' AND '.join(where_parts)}"

        count_query = f"MATCH (n:{self.label}) {where_clause} RETURN count(n) AS total"
        count_records, _, _ = await self.driver.execute_query(
            count_query, **params, database_=self.database
        )
        total = count_records[0]["total"] if count_records else 0

        data_query = f"MATCH (n:{self.label}) {where_clause} RETURN n ORDER BY n.created_at DESC SKIP $skip LIMIT $limit"
        records, _, _ = await self.driver.execute_query(
            data_query, **params, database_=self.database
        )
        items = [node_to_dict(r["n"]) for r in records]
        return items, total

    async def get_unread_count(self, recipient_id: str) -> int:
        query = f"MATCH (n:{self.label} {{recipient_id: $recipient_id, is_read: false}}) RETURN count(n) AS total"
        records, _, _ = await self.driver.execute_query(
            query, recipient_id=recipient_id, database_=self.database
        )
        return records[0]["total"] if records else 0

    async def get_counts(self, recipient_id: str) -> dict[str, int]:
        query = """
        MATCH (n:Notification {recipient_id: $recipient_id})
        RETURN count(n) AS total,
               sum(CASE WHEN n.is_read = false THEN 1 ELSE 0 END) AS unread,
               sum(CASE WHEN n.priority = 'critical' AND n.is_read = false THEN 1 ELSE 0 END) AS critical,
               sum(CASE WHEN n.priority = 'warning' AND n.is_read = false THEN 1 ELSE 0 END) AS warning,
               sum(CASE WHEN n.priority = 'information' AND n.is_read = false THEN 1 ELSE 0 END) AS information
        """
        records, _, _ = await self.driver.execute_query(
            query, recipient_id=recipient_id, database_=self.database
        )
        if records:
            r = records[0]
            return {
                "total": r["total"] or 0,
                "unread": r["unread"] or 0,
                "critical": r["critical"] or 0,
                "warning": r["warning"] or 0,
                "information": r["information"] or 0,
            }
        return {"total": 0, "unread": 0, "critical": 0, "warning": 0, "information": 0}

    async def mark_as_read(self, notification_id: str) -> dict[str, Any] | None:
        query = (
            f"MATCH (n:{self.label} {{id: $notification_id}}) "
            f"SET n.is_read = true, n.read_at = $read_at, n.updated_at = $read_at "
            f"RETURN n"
        )
        records, _, _ = await self.driver.execute_query(
            query, notification_id=notification_id, read_at=utc_now(), database_=self.database
        )
        return node_to_dict(records[0]["n"]) if records else None

    async def mark_all_as_read(self, recipient_id: str) -> bool:
        query = (
            f"MATCH (n:{self.label} {{recipient_id: $recipient_id, is_read: false}}) "
            f"SET n.is_read = true, n.read_at = $read_at, n.updated_at = $read_at "
            f"RETURN count(n) AS cnt"
        )
        records, _, _ = await self.driver.execute_query(
            query, recipient_id=recipient_id, read_at=utc_now(), database_=self.database
        )
        return (records[0]["cnt"] > 0) if records else False

    async def bulk_mark_as_read(self, notification_ids: list[str]) -> bool:
        query = (
            f"MATCH (n:{self.label}) WHERE n.id IN $ids AND n.is_read = false "
            f"SET n.is_read = true, n.read_at = $read_at, n.updated_at = $read_at "
            f"RETURN count(n) AS cnt"
        )
        records, _, _ = await self.driver.execute_query(
            query, ids=notification_ids, read_at=utc_now(), database_=self.database
        )
        return (records[0]["cnt"] > 0) if records else False
