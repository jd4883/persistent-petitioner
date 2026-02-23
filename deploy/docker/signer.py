"""
Petition signing automation via browser (Playwright).

Fills petition forms with user info from config. Not ready for production use.
Set AUTOMATION_ENABLED=true to attempt signing.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

from config import Settings

log = logging.getLogger(__name__)

AUTOMATION_ENABLED = os.environ.get("AUTOMATION_ENABLED", "false").lower() in ("1", "true", "yes")

FIELD_PATTERNS = {
    "first_name": ["first[_\s]?name", "fname", "given[_\s]?name", "firstName"],
    "last_name": ["last[_\s]?name", "lname", "surname", "family[_\s]?name", "lastName"],
    "email": ["email", "e[-\s]?mail", "your[_\s]?email"],
    "zip_code": ["zip", "zipcode", "postal[_\s]?code", "zip[_\s]?code"],
    "phone": ["phone", "tel", "mobile", "cell"],
    "address": ["address", "street", "addr"],
    "city": ["city", "town"],
    "state": ["state", "region", "province"],
}

USER_FIELD_MAP = {
    "first_name": "user_first_name",
    "last_name": "user_last_name",
    "email": "user_email",
    "zip_code": "user_zip_code",
    "phone": "user_phone",
    "address": "user_address",
    "city": "user_city",
    "state": "user_state",
}


def _get_user_value(settings: Settings, field_key: str) -> str:
    attr = USER_FIELD_MAP.get(field_key)
    return getattr(settings, attr, "") or ""


def _build_field_mapping(settings: Settings, petition_type: Optional[dict]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for our_key, patterns in FIELD_PATTERNS.items():
        value = _get_user_value(settings, our_key)
        if not value:
            continue
        if petition_type and petition_type.get("field_mapping"):
            fm = petition_type["field_mapping"]
            if isinstance(fm, str):
                try:
                    fm = json.loads(fm)
                except (json.JSONDecodeError, TypeError):
                    fm = {}
            form_field = fm.get(our_key) if isinstance(fm, dict) else None
            if form_field:
                mapping[form_field] = value
                continue
        mapping[our_key] = value
    return mapping


def _fill_form_field(page: Any, selector: str, value: str) -> bool:
    try:
        el = page.locator(selector).first
        if el.count() == 0:
            return False
        el.fill(value)
        return True
    except Exception as e:
        log.debug("Could not fill %s: %s", selector, e)
        return False


def _try_fill_form(page: Any, mapping: dict[str, str]) -> int:
    filled = 0
    for our_key, value in mapping.items():
        if not value:
            continue
        selectors = [
            f'input[name="{our_key}"]',
            f'input[id="{our_key}"]',
            f'input[name*="{our_key}"]',
            f'input[id*="{our_key}"]',
            f'input[placeholder*="{our_key.replace("_", " ")}"]',
        ]
        for sel in selectors:
            if _fill_form_field(page, sel, value):
                filled += 1
                break
    return filled


def sign_petition(
    url: str,
    settings: Settings,
    petition_type: Optional[dict] = None,
) -> tuple[bool, str]:
    if not AUTOMATION_ENABLED:
        log.info("Automation disabled (AUTOMATION_ENABLED=false); would attempt: %s", url[:80])
        return False, "Automation disabled"

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log.warning("Playwright not installed; run: pip install playwright && playwright install chromium")
        return False, "Playwright not installed"

    mapping = _build_field_mapping(settings, petition_type)
    if not mapping:
        return False, "No user info configured"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            )
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=10000)

            filled = _try_fill_form(page, mapping)
            log.info("Filled %d fields on %s", filled, url[:60])

            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Sign")',
                'button:has-text("Submit")',
                'a:has-text("Sign")',
                '[class*="submit"]',
                '[class*="sign"]',
            ]
            submitted = False
            for sel in submit_selectors:
                try:
                    btn = page.locator(sel).first
                    if btn.count() > 0:
                        btn.click()
                        submitted = True
                        break
                except Exception:
                    continue

            if not submitted:
                browser.close()
                return False, "Could not find submit button"

            page.wait_for_load_state("networkidle", timeout=15000)
            browser.close()

            return True, f"Filled {filled} fields and submitted"
    except Exception as e:
        log.exception("Signing failed for %s", url[:60])
        return False, str(e)
