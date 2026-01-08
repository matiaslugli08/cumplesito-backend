"""
Simple SMTP email sender for reminders.
Enabled/configured via environment variables (see app.config Settings).
"""

from email.message import EmailMessage
import smtplib
import ssl
from typing import Optional

from app.config import settings


def is_email_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_FROM)


def send_email(to_email: str, subject: str, body_text: str) -> None:
    """
    Send an email via SMTP. Raises on errors.
    """
    if not is_email_configured():
        raise RuntimeError("Email not configured (SMTP_HOST/SMTP_FROM missing)")

    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body_text)

    context = ssl.create_default_context()
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
        if settings.SMTP_USE_TLS:
            server.starttls(context=context)
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(msg)
