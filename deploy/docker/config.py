"""Environment-based configuration. Single source of truth for all settings."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache


def _env(key: str, default: str = "") -> str:
    return (os.environ.get(key) or default).strip()


@dataclass(frozen=True)
class Settings:
    """Configuration from environment. Secrets (email, user info) come from env/Helm secrets."""

    database_url: str = field(
        default_factory=lambda: _env("DATABASE_URL", "sqlite:////app/data/persistent_petitioner.db")
    )

    # Email credentials (IMAP) — use dedicated petition email account
    email_host: str = field(default_factory=lambda: _env("EMAIL_IMAP_HOST", ""))
    email_port: int = field(default_factory=lambda: int(_env("EMAIL_IMAP_PORT", "993")))
    email_user: str = field(default_factory=lambda: _env("EMAIL_USER", ""))
    email_password: str = field(default_factory=lambda: _env("EMAIL_PASSWORD", ""))
    email_use_ssl: bool = field(default_factory=lambda: _env("EMAIL_USE_SSL", "true").lower() in ("1", "true", "yes"))

    # User info for signing petitions — injected via Helm secrets
    user_first_name: str = field(default_factory=lambda: _env("USER_FIRST_NAME", ""))
    user_last_name: str = field(default_factory=lambda: _env("USER_LAST_NAME", ""))
    user_email: str = field(default_factory=lambda: _env("USER_EMAIL", ""))
    user_zip_code: str = field(default_factory=lambda: _env("USER_ZIP_CODE", ""))
    user_phone: str = field(default_factory=lambda: _env("USER_PHONE", ""))
    user_address: str = field(default_factory=lambda: _env("USER_ADDRESS", ""))
    user_city: str = field(default_factory=lambda: _env("USER_CITY", ""))
    user_state: str = field(default_factory=lambda: _env("USER_STATE", ""))

    email_check_interval_minutes: int = field(
        default_factory=lambda: int(_env("EMAIL_CHECK_INTERVAL_MINUTES", "5"))
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
