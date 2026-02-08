"""
Email service for AI Bot Casino.
Uses MailerSend for transactional emails with dry-run support.
"""
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Optional, List, Dict
from settings import settings
from enum import Enum
import logging


class EmailType(str, Enum):
    SEND_OTP_REGISTRATION = "send_otp"
    SEND_OTP_LOGIN = "send_otp_login"
    WELCOME = "welcome"


class EmailRecipient(BaseModel):
    name: Optional[str] = None
    email: str


class EmailService(ABC):
    """Abstract email service interface."""

    @abstractmethod
    def send_email(self, recipient_list: List[EmailRecipient], email_type: EmailType,
                   attributes: Dict = {}) -> None:
        pass


class MailerSendService(EmailService):
    """MailerSend email implementation (v2 SDK)."""

    def __init__(self):
        from mailersend import MailerSendClient
        self.client = MailerSendClient(api_key=settings.email_mailersend_api_key)
        self.from_email = settings.email_from_address or "noreply@aibotcasino.com"

    def send_email(self, recipient_list: List[EmailRecipient], email_type: EmailType,
                   attributes: Dict = {}):
        from mailersend import EmailBuilder

        template_id = settings.email_mailersend_templates.get(email_type.value)
        if not template_id:
            raise ValueError(f"No template ID configured for {email_type.value}")

        subject = settings.email_mailersend_subjects.get(email_type.value, "AI Bot Casino")

        first_recipient = recipient_list[0]
        name = first_recipient.name or "Bot Owner"

        builder = (
            EmailBuilder()
            .from_email(self.from_email, "AI Bot Casino")
            .subject(subject)
            .template(template_id)
        )

        for recipient in recipient_list:
            r_name = recipient.name or "Bot Owner"
            builder.to(recipient.email, r_name)
            personalization_data = {k: str(v) for k, v in (attributes | {"name": r_name}).items() if k != "email"}
            builder.personalize(recipient.email, **personalization_data)

        if settings.email_mailer_dry_run:
            logging.warning(f"DRY RUN: Email {email_type.value} NOT sent (recipient: {first_recipient.email})")
            logging.debug(f"DRY RUN: Attributes: {attributes}")
            return

        email = builder.build()
        try:
            response = self.client.emails.send(email)
        except Exception as e:
            logging.error(f"MailerSend exception: {type(e).__name__}: {e}")
            raise

        status_code = getattr(response, 'status_code', None)
        if status_code == 202:
            logging.info(f"Email sent: {email_type.value} -> {first_recipient.email}")
        elif status_code and 400 <= status_code < 600:
            error_msg = f"MailerSend error (Status: {status_code}): {response}"
            logging.error(error_msg)
            raise Exception(error_msg)


# Global mailer instance
_mailer: Optional[EmailService] = None


def send_email(recipient_list: List[EmailRecipient], email_type: EmailType,
               attributes: Dict = {}):
    """Send an email using the configured mailer."""
    global _mailer
    if _mailer is None:
        if settings.email_mailer_dry_run or not settings.email_mailer:
            # In dry run or no mailer configured, use MailerSend but it'll just log
            _mailer = MailerSendService()
        else:
            _mailer = MailerSendService()
        logging.info("Email service initialized (MailerSend)")

    _mailer.send_email(recipient_list, email_type, attributes)
