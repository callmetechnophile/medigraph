"""Notification endpoints — list, read count, and read mark operations."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, Query, Path
from neo4j import AsyncDriver

from app.database.connection import get_driver
from app.repositories import NotificationRepository
from app.services import NotificationService
from app.schemas import (
    NotificationResponse,
    NotificationCount,
    PaginatedResponse,
    MarkReadRequest,
    SuccessResponse,
)
from app.auth.dependencies import get_current_user
from app.config import get_settings

router = APIRouter(prefix="/notifications", tags=["Notifications"])

def get_notification_service(driver: AsyncDriver = Depends(get_driver)) -> NotificationService:
    repo = NotificationRepository(driver)
    settings = get_settings()
    return NotificationService(
        repo,
        brevo_api_key=settings.brevo_api_key,
        sender_email=settings.brevo_sender_email,
        sender_name=settings.brevo_sender_name
    )

@router.get("", response_model=PaginatedResponse[NotificationResponse])
async def list_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    is_read: bool = Query(None),
    priority: str = Query(""),
    service: NotificationService = Depends(get_notification_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """List notifications sent to the authenticated user."""
    recipient_id = user["user_id"]
    return await service.list_notifications(recipient_id, skip=skip, limit=limit, is_read=is_read, priority=priority)

@router.get("/count", response_model=NotificationCount)
async def get_unread_count(
    service: NotificationService = Depends(get_notification_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """Get total notifications and count of unread notifications by priority."""
    recipient_id = user["user_id"]
    return await service.get_counts(recipient_id)

@router.patch("/{notification_id}/read", response_model=SuccessResponse)
async def mark_as_read(
    notification_id: str = Path(...),
    service: NotificationService = Depends(get_notification_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """Mark a notification as read."""
    res = await service.mark_as_read(notification_id)
    return SuccessResponse(message=res["message"], data={"success": res["success"]})

@router.post("/mark-all-read", response_model=SuccessResponse)
async def mark_all_read(
    service: NotificationService = Depends(get_notification_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """Mark all unread notifications for the authenticated user as read."""
    recipient_id = user["user_id"]
    res = await service.mark_all_as_read(recipient_id)
    return SuccessResponse(message=res["message"], data={"success": res["success"]})

@router.post("/bulk-read", response_model=SuccessResponse)
async def bulk_mark_read(
    data: MarkReadRequest,
    service: NotificationService = Depends(get_notification_service),
    user: dict[str, Any] = Depends(get_current_user)
):
    """Bulk mark a set of notification IDs as read."""
    res = await service.bulk_mark_as_read(data.notification_ids)
    return SuccessResponse(message=res["message"], data={"success": res["success"]})
