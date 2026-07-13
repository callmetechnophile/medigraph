"""Notification service — Orchestrates in-app notifications and Brevo email/SMS."""

from __future__ import annotations

from typing import Any
from fastapi import HTTPException
import structlog
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

from app.repositories import NotificationRepository
from app.schemas import (
    NotificationCreate,
    NotificationResponse,
    NotificationCount,
    PaginatedResponse,
)
from app.utils.helpers import generate_id, utc_now

logger = structlog.get_logger(__name__)

class NotificationService:
    def __init__(
        self,
        notification_repo: NotificationRepository,
        brevo_api_key: str,
        sender_email: str,
        sender_name: str,
    ):
        self.notification_repo = notification_repo
        self.sender_email = sender_email
        self.sender_name = sender_name

        # Init Brevo SDK
        if brevo_api_key:
            self.configuration = sib_api_v3_sdk.Configuration()
            self.configuration.api_key['api-key'] = brevo_api_key
            self.brevo_api = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(self.configuration))
            self.brevo_sms_api = sib_api_v3_sdk.TransactionalSMSApi(sib_api_v3_sdk.ApiClient(self.configuration))
        else:
            self.brevo_api = None
            self.brevo_sms_api = None
            logger.warning("brevo.not_configured", message="Brevo API key missing. Emails and SMS will not be sent.")

    async def create_notification(self, data: NotificationCreate) -> NotificationResponse:
        res = await self.notification_repo.create(data.model_dump())
        notification = NotificationResponse(**res)

        # Trigger external notification channels if critical or warning
        if notification.priority in ["critical", "warning"]:
            # For simplicity, we hook this to email dispatch if recipient info can be resolved.
            # In a real environment, you would query recipient email/phone from Clerk or DB first.
            pass

        return notification

    async def list_notifications(self, recipient_id: str, skip: int = 0, limit: int = 20, is_read: bool | None = None, priority: str = "") -> PaginatedResponse[NotificationResponse]:
        items, total = await self.notification_repo.get_by_recipient(
            recipient_id, skip=skip, limit=limit, is_read=is_read, priority=priority
        )
        return PaginatedResponse(
            items=[NotificationResponse(**i) for i in items],
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total,
        )

    async def get_counts(self, recipient_id: str) -> NotificationCount:
        counts = await self.notification_repo.get_counts(recipient_id)
        return NotificationCount(**counts)

    async def mark_as_read(self, notification_id: str) -> dict[str, Any]:
        res = await self.notification_repo.mark_as_read(notification_id)
        if not res:
            raise HTTPException(status_code=404, detail="Notification not found.")
        return {"message": "Notification marked as read.", "success": True}

    async def mark_all_as_read(self, recipient_id: str) -> dict[str, Any]:
        success = await self.notification_repo.mark_all_as_read(recipient_id)
        return {"message": "All notifications marked as read.", "success": success}

    async def bulk_mark_as_read(self, notification_ids: list[str]) -> dict[str, Any]:
        success = await self.notification_repo.bulk_mark_as_read(notification_ids)
        return {"message": "Selected notifications marked as read.", "success": success}

    async def send_email(self, to_email: str, to_name: str, subject: str, html_content: str) -> bool:
        if not self.brevo_api:
            logger.info("brevo.email_skipped", to=to_email, subject=subject)
            return False

        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[sib_api_v3_sdk.SendSmtpEmailTo(email=to_email, name=to_name)],
            sender=sib_api_v3_sdk.SendSmtpEmailSender(email=self.sender_email, name=self.sender_name),
            subject=subject,
            html_content=html_content
        )

        try:
            self.brevo_api.send_transac_email(send_smtp_email)
            logger.info("brevo.email_sent", to=to_email, subject=subject)
            return True
        except ApiException as e:
            logger.error("brevo.email_failed", error=str(e))
            return False

    async def send_sms(self, to_phone: str, message: str) -> bool:
        if not self.brevo_sms_api:
            logger.info("brevo.sms_skipped", to=to_phone)
            return False

        send_transac_sms = sib_api_v3_sdk.SendTransacSms(
            sender=self.sender_name[:11],  # Max 11 characters
            recipient=to_phone,
            content=message
        )

        try:
            self.brevo_sms_api.send_transac_sms(send_transac_sms)
            logger.info("brevo.sms_sent", to=to_phone)
            return True
        except ApiException as e:
            logger.error("brevo.sms_failed", error=str(e))
            return False
