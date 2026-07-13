"""Brevo email/SMS integration client wrapper using Sendinblue SDK."""

from __future__ import annotations

import structlog
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

logger = structlog.get_logger(__name__)

class BrevoClient:
    def __init__(self, api_key: str, sender_email: str, sender_name: str):
        self.sender_email = sender_email
        self.sender_name = sender_name
        
        if api_key:
            self.configuration = sib_api_v3_sdk.Configuration()
            self.configuration.api_key['api-key'] = api_key
            self.email_api = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(self.configuration))
            self.sms_api = sib_api_v3_sdk.TransactionalSMSApi(sib_api_v3_sdk.ApiClient(self.configuration))
        else:
            self.email_api = None
            self.sms_api = None
            logger.warning("brevo.client.disabled", message="No API key supplied.")

    def send_email(self, to_email: str, to_name: str, subject: str, html_content: str) -> bool:
        if not self.email_api:
            logger.info("brevo.email.skipped", to=to_email)
            return False

        send_email_req = sib_api_v3_sdk.SendSmtpEmail(
            to=[sib_api_v3_sdk.SendSmtpEmailTo(email=to_email, name=to_name)],
            sender=sib_api_v3_sdk.SendSmtpEmailSender(email=self.sender_email, name=self.sender_name),
            subject=subject,
            html_content=html_content
        )
        try:
            self.email_api.send_transac_email(send_email_req)
            return True
        except ApiException as e:
            logger.error("brevo.email.exception", error=str(e))
            return False

    def send_sms(self, to_phone: str, message: str) -> bool:
        if not self.sms_api:
            logger.info("brevo.sms.skipped", to=to_phone)
            return False

        send_sms_req = sib_api_v3_sdk.SendTransacSms(
            sender=self.sender_name[:11],
            recipient=to_phone,
            content=message
        )
        try:
            self.sms_api.send_transac_sms(send_sms_req)
            return True
        except ApiException as e:
            logger.error("brevo.sms.exception", error=str(e))
            return False
