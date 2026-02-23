#!/usr/bin/env python3
"""
Persistent Petitioner entrypoint.

  serve     — Run FastAPI (health, UI, API) and background email checker.
  (default) — Run email check once (one-shot / cron).
"""
from __future__ import annotations

import argparse
import logging
import threading
import time
from typing import NoReturn

from config import get_settings
from db import (
    init_db,
    is_already_processed,
    list_petition_types,
    record_processed,
    get_pending_petitions,
    update_petition_status,
)
from email_client import fetch_petition_emails
from signer import sign_petition

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-14s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def _run_email_check() -> None:
    settings = get_settings()
    if not settings.database_url:
        log.warning("DATABASE_URL not set; skipping")
        return
    init_db(settings.database_url)

    for email_data in fetch_petition_emails(settings):
        msg_id = email_data.get("message_id", "")
        if is_already_processed(settings.database_url, msg_id):
            continue

        if not email_data.get("is_simple_petition"):
            log.info(
                "Skipping (filter): %s — %s",
                email_data.get("subject", "")[:60],
                email_data.get("filter_reason", ""),
            )
            record_processed(
                settings.database_url,
                email_message_id=msg_id,
                subject=email_data.get("subject"),
                petition_url=email_data.get("urls", [None])[0] if email_data.get("urls") else None,
                status="skipped",
                notes=email_data.get("filter_reason"),
            )
            continue

        urls = email_data.get("urls", [])
        petition_url = urls[0] if urls else None
        record_processed(
            settings.database_url,
            email_message_id=msg_id,
            subject=email_data.get("subject"),
            petition_url=petition_url,
            status="pending",
            notes=None,
        )
        log.info("Queued for signing: %s", email_data.get("subject", "")[:60])


def _run_signer() -> None:
    settings = get_settings()
    if not settings.database_url:
        return
    init_db(settings.database_url)

    pending = get_pending_petitions(settings.database_url, limit=5)
    types_by_id = {t["id"]: t for t in list_petition_types(settings.database_url)}

    for p in pending:
        url = p.get("petition_url")
        if not url:
            continue
        pt_id = p.get("petition_type_id")
        pt = types_by_id.get(pt_id) if pt_id else None
        success, msg = sign_petition(url, settings, pt)
        update_petition_status(
            settings.database_url,
            p["id"],
            status="signed" if success else "failed",
            notes=msg,
        )
        log.info("Signing %s: %s — %s", "OK" if success else "FAIL", p.get("subject", "")[:40], msg)


def _job_loop(interval_minutes: int) -> NoReturn:
    settings = get_settings()
    while True:
        try:
            _run_email_check()
            _run_signer()
        except Exception:
            log.exception("Job loop failed")
        time.sleep(max(60, interval_minutes * 60))


parser = argparse.ArgumentParser(prog="persistent-petitioner")
sub = parser.add_subparsers(dest="command")

serve_p = sub.add_parser("serve", help="run web app and background email checker")
serve_p.add_argument("--host", default="0.0.0.0")
serve_p.add_argument("--port", type=int, default=8080)
serve_p.add_argument("--interval", type=int, default=None)

args = parser.parse_args()

if args.command == "serve":
    import uvicorn

    from app import app

    settings = get_settings()
    interval = args.interval if args.interval is not None else settings.email_check_interval_minutes
    threading.Thread(target=_job_loop, args=(interval,), daemon=True).start()
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
else:
    _run_email_check()
    _run_signer()
