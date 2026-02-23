"""Email client for reading petition emails. IMAP-based; filters for simple petitions only."""
from __future__ import annotations

import email
import imaplib
import logging
import re
from email.header import decode_header
from typing import Iterator, Optional

from config import Settings

log = logging.getLogger(__name__)


def _decode_header_value(header: Optional[str]) -> str:
    if not header:
        return ""
    decoded_parts = decode_header(header)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            result.append(str(part))
    return "".join(result)


def _extract_urls(text: str) -> list[str]:
    return re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE).findall(text)


def _is_simple_petition(subject: str, body: str) -> tuple[bool, str]:
    subject_lower = subject.lower()
    body_lower = body.lower()

    survey_keywords = ["survey", "poll", "quiz", "feedback form", "tell us about"]
    for kw in survey_keywords:
        if kw in subject_lower or kw in body_lower[:2000]:
            return False, f"Looks like a survey (contains '{kw}')"

    layered_keywords = [
        "select all that apply",
        "multiple choice",
        "rate each",
        "on a scale of",
        "section 1 of",
        "section 2 of",
        "step 1 of",
        "step 2 of",
    ]
    for kw in layered_keywords:
        if kw in body_lower[:3000]:
            return False, f"Layered form (contains '{kw}')"

    petition_keywords = [
        "sign the petition",
        "add your name",
        "sign now",
        "petition",
        "email your senator",
        "contact your representative",
        "tell congress",
        "one click",
        "quick action",
    ]
    for kw in petition_keywords:
        if kw in subject_lower or kw in body_lower[:2000]:
            return True, f"Simple petition (contains '{kw}')"

    return False, "No clear petition signal; skipping to avoid complex forms"


def fetch_petition_emails(settings: Settings) -> Iterator[dict]:
    if not settings.email_host or not settings.email_user or not settings.email_password:
        log.warning("Email credentials not configured; skipping fetch")
        return

    try:
        if settings.email_use_ssl:
            mail = imaplib.IMAP4_SSL(settings.email_host, settings.email_port)
        else:
            mail = imaplib.IMAP4(settings.email_host, settings.email_port)

        mail.login(settings.email_user, settings.email_password)
        mail.select("INBOX")

        _, msg_nums = mail.search(None, "UNSEEN")
        for num in msg_nums[0].split():
            if not num:
                continue
            try:
                _, data = mail.fetch(num, "(RFC822)")
                raw = data[0][1]
                msg = email.message_from_bytes(raw)

                subject = _decode_header_value(msg.get("Subject", ""))
                message_id = msg.get("Message-ID", "").strip("<>")

                body_parts = []
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            payload = part.get_payload(decode=True)
                            if payload:
                                body_parts.append(payload.decode("utf-8", errors="replace"))
                else:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        body_parts.append(payload.decode("utf-8", errors="replace"))

                body = "\n".join(body_parts)
                is_simple, reason = _is_simple_petition(subject, body)
                urls = _extract_urls(body)

                yield {
                    "message_id": message_id,
                    "subject": subject,
                    "body_preview": body[:500],
                    "urls": urls,
                    "is_simple_petition": is_simple,
                    "filter_reason": reason,
                }
            except Exception:
                log.exception("Error processing email %s", num)

        mail.logout()
    except Exception:
        log.exception("IMAP connection failed")
