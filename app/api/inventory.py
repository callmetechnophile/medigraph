"""Inventory endpoints — Stock items, low-stock warnings, and batch voice updates."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query, Path
from neo4j import AsyncDriver

from app.database.connection import get_driver
from app.repositories import InventoryRepository, NotificationRepository
from app.services import InventoryService
from app.schemas import (
    InventoryItemCreate,
    InventoryItemUpdate,
    InventoryResponse,
    PaginatedResponse,
    MedicineCreate,
    MedicineResponse,
    BatchStockUpdate,
)
from app.auth.dependencies import require_roles

router = APIRouter(tags=["Inventory"])

def get_inventory_service(driver: AsyncDriver = Depends(get_driver)) -> InventoryService:
    inv_repo = InventoryRepository(driver)
    notif_repo = NotificationRepository(driver)
    return InventoryService(inv_repo, notif_repo)

@router.post("/hospitals/{hospital_id}/inventory", response_model=InventoryResponse)
async def add_inventory_item(
    data: InventoryItemCreate,
    hospital_id: str = Path(...),
    service: InventoryService = Depends(get_inventory_service),
    user: dict[str, Any] = Depends(require_roles("hospital_staff", "hospital_admin", "system_admin"))
):
    """Add medicine to hospital inventory."""
    return await service.add_item(hospital_id, data)

@router.get("/hospitals/{hospital_id}/inventory", response_model=PaginatedResponse[InventoryResponse])
async def list_inventory(
    hospital_id: str = Path(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    low_stock_only: bool = Query(False),
    service: InventoryService = Depends(get_inventory_service),
    user: dict[str, Any] = Depends(require_roles("hospital_staff", "hospital_admin", "system_admin"))
):
    """List inventory items, supporting low stock filtering and search queries."""
    return await service.list_items(hospital_id, skip=skip, limit=limit, search=search, low_stock_only=low_stock_only)

@router.get("/inventory/{item_id}", response_model=InventoryResponse)
async def get_inventory_item(
    item_id: str = Path(...),
    service: InventoryService = Depends(get_inventory_service),
    user: dict[str, Any] = Depends(require_roles("hospital_staff", "hospital_admin", "system_admin"))
):
    """Get inventory item details."""
    return await service.get_item(item_id)

@router.put("/inventory/{item_id}", response_model=InventoryResponse)
async def update_inventory_item(
    data: InventoryItemUpdate,
    item_id: str = Path(...),
    service: InventoryService = Depends(get_inventory_service),
    user: dict[str, Any] = Depends(require_roles("hospital_staff", "hospital_admin", "system_admin"))
):
    """Update inventory item properties."""
    return await service.update_item(item_id, data)

@router.patch("/inventory/{item_id}/stock", response_model=InventoryResponse)
async def update_stock_level(
    current_stock: int = Query(..., ge=0),
    item_id: str = Path(...),
    service: InventoryService = Depends(get_inventory_service),
    user: dict[str, Any] = Depends(require_roles("hospital_staff", "hospital_admin", "system_admin"))
):
    """Directly adjust stock level for a medicine inventory item."""
    return await service.update_stock(item_id, current_stock)

@router.post("/hospitals/{hospital_id}/inventory/batch-update", response_model=list[InventoryResponse])
async def batch_update_stock(
    data: BatchStockUpdate,
    hospital_id: str = Path(...),
    service: InventoryService = Depends(get_inventory_service),
    user: dict[str, Any] = Depends(require_roles("hospital_staff", "hospital_admin", "system_admin"))
):
    """Batch update stock levels (typically routed from voice updates)."""
    return await service.batch_update_stock(hospital_id, data)

@router.get("/hospitals/{hospital_id}/inventory/low-stock", response_model=list[InventoryResponse])
async def get_low_stock_alerts(
    hospital_id: str = Path(...),
    service: InventoryService = Depends(get_inventory_service),
    user: dict[str, Any] = Depends(require_roles("hospital_staff", "hospital_admin", "system_admin"))
):
    """List inventory items that fall below their reorder levels."""
    return await service.get_low_stock_alerts(hospital_id)

@router.post("/medicines", response_model=MedicineResponse)
async def add_medicine(
    data: MedicineCreate,
    service: InventoryService = Depends(get_inventory_service),
    user: dict[str, Any] = Depends(require_roles("hospital_admin", "system_admin"))
):
    """Add a new medicine definition to the central database catalog."""
    return await service.add_medicine(data)

@router.get("/medicines", response_model=PaginatedResponse[MedicineResponse])
async def list_medicines(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    service: InventoryService = Depends(get_inventory_service),
    user: dict[str, Any] = Depends(require_roles("hospital_staff", "hospital_admin", "system_admin"))
):
    """List central medicine catalog registry."""
    return await service.list_medicines(skip=skip, limit=limit, search=search)
