"""
sender.py — Sends the digest email via Gmail SMTP.

Uses Gmail App Password (NOT your normal Gmail password).
Setup: https://myaccount.google.com/apppasswords
  1. Enable 2FA on your Google account.
  2. Create an App Password for "Mail" / "Mac" (or Other).
  3. Put the 16-char password in .env as GMAIL_APP_PASSWORD.

The email is sent with X-Priority: 1 (High) headers.
"""
from __future__ import annotations

import logging
import os
import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def send_digest(html_body: str, to_email: str, subject: str) -> bool:
    """
    Sends an HTML email via Gmail SMTP.
    Returns True on success, False on failure.
    """
    gmail_user = os.getenv("GMAIL_ADDRESS", "")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD", "")

    if not gmail_user or not gmail_password:
        logger.error(
            "sender: GMAIL_ADDRESS or GMAIL_APP_PASSWORD not set in .env — cannot send email"
        )
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"FDE Job Digest <{gmail_user}>"
    msg["To"] = to_email
    msg["X-Priority"] = "1"
    msg["X-MSMail-Priority"] = "High"
    msg["Importance"] = "High"

    # Plain-text fallback
    plain = (
        f"FDE Job Digest — {date.today()}\n"
        "See the HTML version for full details.\n"
        f"Sent to: {to_email}"
    )
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, to_email, msg.as_string())
        logger.info("Email sent to %s", to_email)
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error(
            "Gmail auth failed. Make sure you're using an App Password, "
            "not your regular Gmail password."
        )
        return False
    except Exception as exc:
        logger.error("Failed to send email: %s", exc)
        return False
