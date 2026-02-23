# Persistent Petitioner

Automate signing political petitions from a dedicated inbox. Reads petition emails via IMAP, filters simple petitions (sign-on, email senators), and optionally fills forms via Playwright.

## Features

- **IMAP email client** — fetches petition emails from Gmail (or other IMAP)
- **Simple-petition filter** — skips complex surveys; processes sign-on / email-senator style petitions
- **Playwright signer** — opt-in browser automation (`AUTOMATION_ENABLED=true`)
- **Web UI** — manage petition types, view processed petitions
- **PostgreSQL / SQLite** — SQLAlchemy; configurable via `DATABASE_URL`
- **Helm chart** — Kubernetes deployment with External Secrets / 1Password support

## Quick start

```bash
cd deploy/docker
pip install -r requirements.txt
python main.py serve --host 0.0.0.0 --port 8080
```

## Environment variables

| Variable | Description |
|----------|-------------|
| `EMAIL_IMAP_HOST` | IMAP host (e.g. `imap.gmail.com`) |
| `EMAIL_USER` | Email address |
| `EMAIL_PASSWORD` | App password (not account password) |
| `USER_FIRST_NAME`, `USER_LAST_NAME`, `USER_EMAIL`, `USER_ZIP_CODE` | Form fill data |
| `USER_PHONE` | Optional |
| `DATABASE_URL` | PostgreSQL or SQLite (default: `sqlite:////app/data/persistent_petitioner.db`) |
| `AUTOMATION_ENABLED` | `true` to enable Playwright signing |
| `EMAIL_CHECK_INTERVAL_MINUTES` | Poll interval (default: 5) |

## Gmail setup

1. Create a dedicated Gmail address (e.g. `petitions@example.com`)
2. Forward petition emails to it or use filters
3. Enable 2FA, then create an App Password
4. Use the App Password as `EMAIL_PASSWORD`

## Deploy

- **Docker:** See `deploy/docker/README.md`
- **Helm:** See `deploy/helm/README.md`
