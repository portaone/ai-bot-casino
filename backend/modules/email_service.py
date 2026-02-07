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
    SEND_OTP_REGISTRATION = "send_otp_registration"
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
    """MailerSend email implementation."""

    def __init__(self):
        self.api_key = settings.email_mailersend_api_key

    def send_email(self, recipient_list: List[EmailRecipient], email_type: EmailType,
                   attributes: Dict = {}):
        from mailersend import emails as mailersend_emails
        import json

        mailer = mailersend_emails.NewEmail(self.api_key)
        mail_body = {}

        mail_from = {
            "name": "AI Bot Casino",
            "email": settings.email_from_address,
        }

        recipients = []
        variables = []
        for x in recipient_list:
            name = x.name or "Bot Owner"
            recipients.append({"name": name, "email": x.email})
            variables.append({"email": x.email, "data": attributes | {"name": name}})

        mailer.set_mail_from(mail_from, mail_body)
        mailer.set_mail_to(recipients, mail_body)

        subject = settings.email_mailersend_subjects.get(email_type.value)
        if not subject:
            subject = "AI Bot Casino"
        mailer.set_subject(subject, mail_body)

        template_id = settings.email_mailersend_templates.get(email_type.value)
        if not template_id:
            raise ValueError(f"No template ID configured for {email_type.value}")
        mailer.set_template(template_id, mail_body)
        mailer.set_personalization(variables, mail_body)

        if settings.email_mailer_dry_run:
            logging.warning(f"DRY RUN: Email {email_type.value} NOT sent (recipient: {recipients[0]['email']})")
            logging.debug(f"DRY RUN: Variables: {variables}")
        else:
            try:
                res = mailer.send(mail_body)
            except Exception as e:
                logging.error(f"MailerSend exception: {type(e).__name__}: {str(e)}")
                raise

            status_code = None
            error_details = None

            if isinstance(res, int):
                status_code = res
            elif isinstance(res, str):
                parts = res.split('\n', 1)
                try:
                    status_code = int(parts[0])
                    if len(parts) > 1:
                        try:
                            error_json = json.loads(parts[1])
                            error_details = error_json.get('message', parts[1])
                        except json.JSONDecodeError:
                            error_details = parts[1]
                except (ValueError, IndexError):
                    raise Exception(f"Invalid MailerSend response: {res}")

            if status_code == 202:
                logging.info(f"Email sent: {email_type.value} -> {recipients[0]['email']}")
            elif status_code == 401:
                error_msg = f"MailerSend authentication failed (Status: 401)"
                if error_details:
                    error_msg += f": {error_details}"
                logging.error(error_msg)
                raise Exception(error_msg)
            elif status_code and 400 <= status_code < 600:
                error_msg = f"MailerSend error (Status: {status_code})"
                if error_details:
                    error_msg += f": {error_details}"
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
