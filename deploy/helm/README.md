# Persistent Petitioner Helm chart

Deploy petition automation with IMAP email and optional Playwright signing.

## Secrets

Create a Secret (or use External Secrets / 1Password) with:

- `EMAIL_IMAP_HOST`, `EMAIL_USER`, `EMAIL_PASSWORD` — IMAP credentials
- `USER_FIRST_NAME`, `USER_LAST_NAME`, `USER_EMAIL`, `USER_ZIP_CODE` — form fill data
- `USER_PHONE` (optional)
- `DATABASE_URL` (optional; defaults to SQLite in `/app/data`)
- `AUTOMATION_ENABLED` (optional; set to `true` to enable Playwright signing)

## Install

```bash
helm install persistent-petitioner ./deploy/helm -n persistent-petitioner --create-namespace -f my-values.yaml
```
