"""FastAPI app: health, web UI, and REST API for petition types and status."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel

import db
from config import get_settings

app = FastAPI(title="Persistent Petitioner", version="0.1.0")
_settings = get_settings()
_UI_HTML = (Path(__file__).parent / "templates" / "index.html").read_text()


@app.on_event("startup")
def _init_database() -> None:
    db.init_db(_settings.database_url)


def _db_url() -> str:
    if not _settings.database_url:
        raise HTTPException(503, "DATABASE_URL is not set")
    return _settings.database_url


@app.get("/health", response_class=PlainTextResponse)
def health() -> str:
    return "ok"


@app.get("/", response_class=HTMLResponse)
def root() -> HTMLResponse:
    return HTMLResponse(_UI_HTML)


class PetitionTypeIn(BaseModel):
    name: str
    description: Optional[str] = None
    field_mapping: Optional[dict[str, str]] = None
    url_pattern: Optional[str] = None
    enabled: bool = True


class PetitionTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    field_mapping: Optional[dict[str, str]] = None
    url_pattern: Optional[str] = None
    enabled: Optional[bool] = None


@app.get("/api/petition-types")
def list_petition_types() -> list[dict]:
    return db.list_petition_types(_db_url())


@app.post("/api/petition-types", status_code=201)
def add_petition_type(payload: PetitionTypeIn) -> dict:
    ptid = db.add_petition_type(
        _db_url(),
        name=payload.name,
        description=payload.description,
        field_mapping=payload.field_mapping,
        url_pattern=payload.url_pattern,
        enabled=payload.enabled,
    )
    if ptid is None:
        raise HTTPException(500, "Failed to add petition type")
    return {"id": ptid, "name": payload.name}


@app.put("/api/petition-types/{type_id}")
def update_petition_type(type_id: int, payload: PetitionTypeUpdate) -> dict:
    if not db.update_petition_type(
        _db_url(),
        type_id,
        name=payload.name,
        description=payload.description,
        field_mapping=payload.field_mapping,
        url_pattern=payload.url_pattern,
        enabled=payload.enabled,
    ):
        raise HTTPException(404, "Petition type not found")
    return {"id": type_id, "updated": True}


@app.delete("/api/petition-types/{type_id}")
def delete_petition_type_endpoint(type_id: int) -> dict:
    if not db.delete_petition_type(_db_url(), type_id):
        raise HTTPException(404, "Petition type not found")
    return {"deleted": type_id}


@app.get("/api/processed")
def list_processed(limit: int = 100) -> list[dict]:
    return db.list_processed(_db_url(), limit=min(limit, 500))


@app.get("/api/status")
def status() -> dict:
    return {
        "email_configured": bool(
            _settings.email_host and _settings.email_user and _settings.email_password
        ),
        "user_info_configured": bool(
            _settings.user_first_name and _settings.user_last_name and _settings.user_email
        ),
        "database_url_set": bool(_settings.database_url),
    }
