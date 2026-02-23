"""Database layer for petition types and processed petitions. Supports SQLite and PostgreSQL via SQLAlchemy."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    Boolean,
    create_engine,
    delete,
    insert,
    select,
    update,
)
from sqlalchemy.engine import Engine

log = logging.getLogger(__name__)

metadata = MetaData()

petition_types = Table(
    "petition_types",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(255), nullable=False),
    Column("description", Text),
    Column("field_mapping", Text),
    Column("url_pattern", String(512)),
    Column("enabled", Boolean, default=True),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
)

processed_petitions = Table(
    "processed_petitions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("email_message_id", String(512), unique=True),
    Column("petition_type_id", Integer),
    Column("petition_url", Text),
    Column("subject", String(512)),
    Column("signed_at", DateTime, default=datetime.utcnow),
    Column("status", String(50), default="signed"),
    Column("notes", Text),
)

_engine: Optional[Engine] = None


def _normalize_url(db_url: str) -> str:
    if db_url.startswith("postgresql://"):
        return db_url.replace("postgresql://", "postgresql+pg8000://", 1)
    return db_url


def get_engine(db_url: str) -> Engine:
    global _engine
    if _engine is not None:
        return _engine
    url = _normalize_url(db_url)
    if url.startswith("sqlite"):
        path = url.removeprefix("sqlite:///")
        if path:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    _engine = create_engine(url, pool_pre_ping=True)
    metadata.create_all(_engine)
    log.info("Database initialized: %s", url.split("@")[-1] if "@" in url else url)
    return _engine


def init_db(db_url: str) -> bool:
    if not db_url:
        return False
    try:
        get_engine(db_url)
        return True
    except Exception:
        log.exception("Failed to initialize database")
        return False


def list_petition_types(db_url: str) -> list[dict[str, Any]]:
    engine = get_engine(db_url)
    with engine.connect() as conn:
        rows = conn.execute(select(petition_types).order_by(petition_types.c.name)).mappings().all()
    return [dict(r) for r in rows]


def add_petition_type(
    db_url: str,
    *,
    name: str,
    description: Optional[str] = None,
    field_mapping: Optional[dict] = None,
    url_pattern: Optional[str] = None,
    enabled: bool = True,
) -> Optional[int]:
    engine = get_engine(db_url)
    fm = json.dumps(field_mapping) if field_mapping else None
    with engine.begin() as conn:
        result = conn.execute(
            insert(petition_types).values(
                name=name,
                description=description,
                field_mapping=fm,
                url_pattern=url_pattern,
                enabled=enabled,
            )
        )
        return result.inserted_primary_key[0] if result.inserted_primary_key else None


def update_petition_type(
    db_url: str,
    type_id: int,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    field_mapping: Optional[dict] = None,
    url_pattern: Optional[str] = None,
    enabled: Optional[bool] = None,
) -> bool:
    engine = get_engine(db_url)
    values = {}
    if name is not None:
        values["name"] = name
    if description is not None:
        values["description"] = description
    if field_mapping is not None:
        values["field_mapping"] = json.dumps(field_mapping)
    if url_pattern is not None:
        values["url_pattern"] = url_pattern
    if enabled is not None:
        values["enabled"] = enabled
    if not values:
        return True
    with engine.begin() as conn:
        result = conn.execute(update(petition_types).where(petition_types.c.id == type_id).values(**values))
        return result.rowcount > 0


def delete_petition_type(db_url: str, type_id: int) -> bool:
    engine = get_engine(db_url)
    with engine.begin() as conn:
        result = conn.execute(delete(petition_types).where(petition_types.c.id == type_id))
        return result.rowcount > 0


def is_already_processed(db_url: str, email_message_id: str) -> bool:
    engine = get_engine(db_url)
    with engine.connect() as conn:
        row = conn.execute(
            select(processed_petitions.c.id).where(processed_petitions.c.email_message_id == email_message_id)
        ).fetchone()
    return row is not None


def record_processed(
    db_url: str,
    *,
    email_message_id: str,
    petition_type_id: Optional[int] = None,
    petition_url: Optional[str] = None,
    subject: Optional[str] = None,
    status: str = "signed",
    notes: Optional[str] = None,
) -> Optional[int]:
    engine = get_engine(db_url)
    with engine.begin() as conn:
        result = conn.execute(
            insert(processed_petitions).values(
                email_message_id=email_message_id,
                petition_type_id=petition_type_id,
                petition_url=petition_url,
                subject=subject,
                status=status,
                notes=notes,
            )
        )
        return result.inserted_primary_key[0] if result.inserted_primary_key else None


def list_processed(db_url: str, limit: int = 100) -> list[dict[str, Any]]:
    engine = get_engine(db_url)
    with engine.connect() as conn:
        rows = conn.execute(
            select(processed_petitions).order_by(processed_petitions.c.signed_at.desc()).limit(limit)
        ).mappings().all()
    return [dict(r) for r in rows]


def get_pending_petitions(db_url: str, limit: int = 10) -> list[dict[str, Any]]:
    engine = get_engine(db_url)
    with engine.connect() as conn:
        rows = conn.execute(
            select(processed_petitions)
            .where(processed_petitions.c.status == "pending")
            .where(processed_petitions.c.petition_url.isnot(None))
            .order_by(processed_petitions.c.signed_at.asc())
            .limit(limit)
        ).mappings().all()
    return [dict(r) for r in rows]


def update_petition_status(
    db_url: str,
    petition_id: int,
    *,
    status: str,
    notes: Optional[str] = None,
) -> bool:
    engine = get_engine(db_url)
    with engine.begin() as conn:
        result = conn.execute(
            update(processed_petitions).where(processed_petitions.c.id == petition_id).values(status=status, notes=notes)
        )
        return result.rowcount > 0
