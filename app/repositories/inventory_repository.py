"""Inventory repository — CRUD and operations for Inventory and Medicines."""

from __future__ import annotations

from typing import Any

from app.repositories.base_repository import BaseRepository
from app.utils.helpers import generate_id, utc_now, node_to_dict

class InventoryRepository(BaseRepository):
    label = "Inventory"
    search_fields = ["batch_number"]

    async def create_medicine(self, medicine_data: dict[str, Any]) -> dict[str, Any]:
        med_id = medicine_data.get("id") or generate_id()
        medicine_data["id"] = med_id
        medicine_data.setdefault("created_at", utc_now())
        medicine_data.setdefault("updated_at", utc_now())

        props = ", ".join(f"{k}: ${k}" for k in medicine_data)
        query = f"CREATE (m:Medicine {{{props}}}) RETURN m"
        records, _, _ = await self.driver.execute_query(
            query, **medicine_data, database_=self.database
        )
        return node_to_dict(records[0]["m"]) if records else medicine_data

    async def get_medicines(self, skip: int = 0, limit: int = 20, search: str = "") -> tuple[list[dict[str, Any]], int]:
        where_str = ""
        params: dict[str, Any] = {"skip": skip, "limit": limit}
        if search:
            where_str = "WHERE toLower(m.name) CONTAINS toLower($search) OR toLower(m.generic_name) CONTAINS toLower($search)"
            params["search"] = search

        count_query = f"MATCH (m:Medicine) {where_str} RETURN count(m) AS total"
        count_records, _, _ = await self.driver.execute_query(
            count_query, **params, database_=self.database
        )
        total = count_records[0]["total"] if count_records else 0

        data_query = f"MATCH (m:Medicine) {where_str} RETURN m ORDER BY m.name ASC SKIP $skip LIMIT $limit"
        records, _, _ = await self.driver.execute_query(
            data_query, **params, database_=self.database
        )
        items = [node_to_dict(r["m"]) for r in records]
        return items, total

    async def create_with_medicine(self, hospital_id: str, inventory_data: dict[str, Any]) -> dict[str, Any]:
        inv_id = inventory_data.get("id") or generate_id()
        inventory_data["id"] = inv_id
        inventory_data.setdefault("created_at", utc_now())
        inventory_data.setdefault("updated_at", utc_now())
        medicine_id = inventory_data.get("medicine_id")

        props = ", ".join(f"{k}: ${k}" for k in inventory_data)
        query = (
            f"MATCH (h:Hospital {{id: $hospital_id}}), (m:Medicine {{id: $medicine_id}}) "
            f"CREATE (i:Inventory {{{props}}}) "
            f"CREATE (h)-[:HAS_INVENTORY]->(i) "
            f"CREATE (i)-[:CONTAINS]->(m) "
            f"RETURN i"
        )
        records, _, _ = await self.driver.execute_query(
            query, hospital_id=hospital_id, medicine_id=medicine_id, **inventory_data, database_=self.database
        )
        return node_to_dict(records[0]["i"]) if records else inventory_data

    async def get_by_hospital(self, hospital_id: str, skip: int = 0, limit: int = 20, low_stock_only: bool = False) -> tuple[list[dict[str, Any]], int]:
        where_parts = ["h.id = $hospital_id"]
        params: dict[str, Any] = {"hospital_id": hospital_id, "skip": skip, "limit": limit}

        if low_stock_only:
            where_parts.append("i.current_stock <= i.reorder_level")

        where_clause = f"WHERE {' AND '.join(where_parts)}"

        count_query = (
            f"MATCH (h:Hospital)-[:HAS_INVENTORY]->(i:Inventory)-[:CONTAINS]->(m:Medicine) "
            f"{where_clause} RETURN count(i) AS total"
        )
        count_records, _, _ = await self.driver.execute_query(
            count_query, **params, database_=self.database
        )
        total = count_records[0]["total"] if count_records else 0

        data_query = (
            f"MATCH (h:Hospital)-[:HAS_INVENTORY]->(i:Inventory)-[:CONTAINS]->(m:Medicine) "
            f"{where_clause} RETURN i, m.name AS medicine_name, m.unit AS medicine_unit "
            f"ORDER BY m.name ASC SKIP $skip LIMIT $limit"
        )
        records, _, _ = await self.driver.execute_query(
            data_query, **params, database_=self.database
        )
        items = []
        for r in records:
            inv_dict = node_to_dict(r["i"])
            inv_dict["medicine_name"] = r["medicine_name"]
            inv_dict["medicine_unit"] = r["medicine_unit"]
            inv_dict["is_low_stock"] = inv_dict["current_stock"] <= inv_dict["reorder_level"]
            items.append(inv_dict)
        return items, total

    async def get_low_stock_items(self, hospital_id: str) -> list[dict[str, Any]]:
        query = (
            "MATCH (h:Hospital {id: $hospital_id})-[:HAS_INVENTORY]->(i:Inventory)-[:CONTAINS]->(m:Medicine) "
            "WHERE i.current_stock <= i.reorder_level "
            "RETURN i, m.name AS medicine_name, m.unit AS medicine_unit"
        )
        records, _, _ = await self.driver.execute_query(
            query, hospital_id=hospital_id, database_=self.database
        )
        items = []
        for r in records:
            inv_dict = node_to_dict(r["i"])
            inv_dict["medicine_name"] = r["medicine_name"]
            inv_dict["medicine_unit"] = r["medicine_unit"]
            inv_dict["is_low_stock"] = True
            items.append(inv_dict)
        return items

    async def update_stock(self, inventory_id: str, new_stock: int) -> dict[str, Any] | None:
        query = (
            "MATCH (i:Inventory {id: $inventory_id}) "
            "SET i.current_stock = $new_stock, i.last_restocked_at = $restocked_at, i.updated_at = $restocked_at "
            "RETURN i"
        )
        records, _, _ = await self.driver.execute_query(
            query, inventory_id=inventory_id, new_stock=new_stock, restocked_at=utc_now(), database_=self.database
        )
        return node_to_dict(records[0]["i"]) if records else None

    async def batch_update_stock(self, hospital_id: str, updates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results = []
        for item in updates:
            med_name = item.get("medicine_name")
            new_stock = item.get("new_stock")
            inv_id = item.get("inventory_id")

            if inv_id:
                res = await self.update_stock(inv_id, new_stock)
                if res:
                    results.append(res)
            elif med_name:
                # Find by medicine name first
                inv_records = await self.find_by_medicine_name(hospital_id, med_name)
                if inv_records:
                    res = await self.update_stock(inv_records[0]["id"], new_stock)
                    if res:
                        results.append(res)
        return results

    async def find_by_medicine_name(self, hospital_id: str, medicine_name: str) -> list[dict[str, Any]]:
        query = (
            "MATCH (h:Hospital {id: $hospital_id})-[:HAS_INVENTORY]->(i:Inventory)-[:CONTAINS]->(m:Medicine) "
            "WHERE toLower(m.name) CONTAINS toLower($medicine_name) OR toLower(m.generic_name) CONTAINS toLower($medicine_name) "
            "RETURN i, m.name AS medicine_name, m.unit AS medicine_unit"
        )
        records, _, _ = await self.driver.execute_query(
            query, hospital_id=hospital_id, medicine_name=medicine_name, database_=self.database
        )
        items = []
        for r in records:
            inv_dict = node_to_dict(r["i"])
            inv_dict["medicine_name"] = r["medicine_name"]
            inv_dict["medicine_unit"] = r["medicine_unit"]
            inv_dict["is_low_stock"] = inv_dict["current_stock"] <= inv_dict["reorder_level"]
            items.append(inv_dict)
        return items

    async def get_expiring_items(self, hospital_id: str, days_ahead: int = 30) -> list[dict[str, Any]]:
        # Cypher date parsing and checking
        query = (
            "MATCH (h:Hospital {id: $hospital_id})-[:HAS_INVENTORY]->(i:Inventory)-[:CONTAINS]->(m:Medicine) "
            "WHERE i.expiry_date IS NOT NULL AND duration.inDays(date(), date(i.expiry_date)).days <= $days_ahead "
            "RETURN i, m.name AS medicine_name, m.unit AS medicine_unit"
        )
        records, _, _ = await self.driver.execute_query(
            query, hospital_id=hospital_id, days_ahead=days_ahead, database_=self.database
        )
        items = []
        for r in records:
            inv_dict = node_to_dict(r["i"])
            inv_dict["medicine_name"] = r["medicine_name"]
            inv_dict["medicine_unit"] = r["medicine_unit"]
            inv_dict["is_low_stock"] = inv_dict["current_stock"] <= inv_dict["reorder_level"]
            items.append(inv_dict)
        return items
