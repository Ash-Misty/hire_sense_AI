import logging
from pathlib import Path
from typing import Any

import httpx
from fastapi.templating import Jinja2Templates

from app.core.config import settings

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="app/templates")


class EmailServiceError(Exception):
    pass


class EmailService:
    def __init__(self) -> None:
        self.enabled = bool(
            settings.MAILJET_API_KEY
            and settings.MAILJET_SECRET_KEY
            and settings.MAIL_FROM_EMAIL
        )
        self.api_key = settings.MAILJET_API_KEY
        self.secret_key = settings.MAILJET_SECRET_KEY
        self.from_email = settings.MAIL_FROM_EMAIL
        self.from_name = settings.MAIL_FROM_NAME or "HireSense AI"
        self.api_url = "https://api.mailjet.com/v3.1/send"

    def send_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        context: dict[str, Any],
    ) -> None:
        if not self.enabled:
            logger.warning(
                "Email service is not configured. "
                "Set MAILJET_API_KEY, MAILJET_SECRET_KEY, and MAIL_FROM_EMAIL in .env"
            )
            return

        template = templates.env.get_template(template_name)
        html_content = template.render(**context)

        payload = {
            "Messages": [
                {
                    "From": {
                        "Email": self.from_email,
                        "Name": self.from_name,
                    },
                    "To": [
                        {
                            "Email": to_email,
                        }
                    ],
                    "Subject": subject,
                    "HTMLPart": html_content,
                }
            ]
        }

        try:
            with httpx.Client() as client:
                response = client.post(
                    self.api_url,
                    json=payload,
                    auth=(self.api_key, self.secret_key),
                    timeout=10.0,
                )
                response.raise_for_status()
        except Exception as exc:
            logger.error("Failed to send email to %s: %s", to_email, exc)
            raise EmailServiceError("Failed to send email.") from exc

    def send_welcome_email(self, to_email: str, name: str) -> None:
        self.send_email(
            to_email=to_email,
            subject="Welcome to HireSense AI",
            template_name="emails/welcome.html",
            context={
                "name": name,
                "frontend_url": "http://localhost:3000",
            },
        )

    def send_verification_email(
        self,
        to_email: str,
        name: str,
        verification_url: str,
        expire_minutes: int,
    ) -> None:
        self.send_email(
            to_email=to_email,
            subject="Verify Your Email Address",
            template_name="emails/verification.html",
            context={
                "name": name,
                "verification_url": verification_url,
                "expire_minutes": expire_minutes,
            },
        )

    def send_password_reset_email(
        self,
        to_email: str,
        name: str,
        reset_url: str,
        expire_minutes: int,
    ) -> None:
        self.send_email(
            to_email=to_email,
            subject="Reset Your Password",
            template_name="emails/password_reset.html",
            context={
                "name": name,
                "reset_url": reset_url,
                "expire_minutes": expire_minutes,
            },
        )
