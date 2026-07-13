"""Inventory service — Orchestrates Stock levels and low-stock alerts."""

from __future__ import annotations

from typing import Any
from fastapi import HTTPException
import structlog

from app.repositories import InventoryRepository, NotificationRepository
from app.schemas import (
    InventoryItemCreate,
    InventoryItemUpdate,
    InventoryResponse,
    PaginatedResponse,
    MedicineCreate,
    MedicineResponse,
    BatchStockUpdate,
)

logger = structlog.get_logger(__name__)

class InventoryService:
    def __init__(self, inventory_repo: InventoryRepository, notification_repo: NotificationRepository):
        self.inventory_repo = inventory_repo
        self.notification_repo = notification_repo

    async def add_medicine(self, data: MedicineCreate) -> MedicineResponse:
        res = await self.inventory_repo.create_medicine(data.model_dump())
        return MedicineResponse(**res)

    async def list_medicines(self, skip: int = 0, limit: int = 20, search: str = "") -> PaginatedResponse[MedicineResponse]:
        items, total = await self.inventory_repo.get_medicines(skip=skip, limit=limit, search=search)
        return PaginatedResponse(
            items=[MedicineResponse(**i) for i in items],
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total,
        )

    async def add_item(self, hospital_id: str, data: InventoryItemCreate) -> InventoryResponse:
        res = await self.inventory_repo.create_with_medicine(hospital_id, data.model_dump())
        return InventoryResponse(**res)

    async def get_item(self, item_id: str) -> InventoryResponse:
        res = await self.inventory_repo.find_by_id(item_id)
        if not res:
            raise HTTPException(status_code=404, detail="Inventory item not found.")
        return InventoryResponse(**res)

    async def update_item(self, item_id: str, data: InventoryItemUpdate) -> InventoryResponse:
        await self.get_item(item_id)
        res = await self.inventory_repo.update(item_id, data.model_dump(exclude_unset=True))
        if not res:
            raise HTTPException(status_code=404, detail="Inventory update failed.")
        return InventoryResponse(**res)

    async def list_items(self, hospital_id: str, skip: int = 0, limit: int = 20, search: str = "", low_stock_only: bool = False) -> PaginatedResponse[InventoryResponse]:
        items, total = await self.inventory_repo.get_by_hospital(
            hospital_id, skip=skip, limit=limit, low_stock_only=low_stock_only
        )
        return PaginatedResponse(
            items=[InventoryResponse(**i) for i in items],
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total,
        )

    async def update_stock(self, inventory_id: str, new_stock: int) -> InventoryResponse:
        inv = await self.get_item(inventory_id)
        res = await self.inventory_repo.update_stock(inventory_id, new_stock)
        if not res:
            raise HTTPException(status_code=404, detail="Failed to update stock.")

        # Check if now low stock and create alert notification
        if new_stock <= inv.reorder_level:
            await self._trigger_low_stock_alert(inv.hospital_id, inv.medicine_name, new_stock, inv.reorder_level)

        return InventoryResponse(**res)

    async def batch_update_stock(self, hospital_id: str, updates: BatchStockUpdate) -> list[InventoryResponse]:
        res_list = await self.inventory_repo.batch_update_stock(hospital_id, updates.updates)
        items = []
        for r in res_list:
            inv = InventoryResponse(**r)
            items.append(inv)
            if inv.current_stock <= inv.reorder_level:
                await self._trigger_low_stock_alert(hospital_id, inv.medicine_name, inv.current_stock, inv.reorder_level)
        return items

    async def get_low_stock_alerts(self, hospital_id: str) -> list[InventoryResponse]:
        items = await self.inventory_repo.get_low_stock_items(hospital_id)
        return [InventoryResponse(**i) for i in items]

    async def _trigger_low_stock_alert(self, hospital_id: str, medicine_name: str, current_stock: int, reorder_level: int) -> None:
        alert_data = {
            "recipient_id": hospital_id,
            "recipient_type": "hospital",
            "title": f"Low Stock Alert: {medicine_name}",
            "message": f"Stock of {medicine_name} is critical: {current_stock} remaining (Reorder Level: {reorder_level})",
            "priority": "warning",
            "source": "inventory",
            "metadata": {
                "medicine_name": medicine_name,
                "current_stock": current_stock,
                "reorder_level": reorder_level,
            }
        }
        await self.notification_repo.create(alert_data)
        logger.info("inventory.low_stock.alert_created", hospital_id=hospital_id, medicine=medicine_name)
# Removed duplicate class definition
