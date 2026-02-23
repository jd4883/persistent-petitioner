# Persistent Petitioner — Docker

Run the persistent petitioner app locally or via Docker.

## Quick start

```bash
cd deploy/docker
pip install -r requirements.txt
python main.py serve --host 0.0.0.0 --port 8080
```

## Docker

```bash
docker build -t persistent-petitioner .
docker run -p 8080:8080 \
  -e EMAIL_IMAP_HOST=imap.gmail.com \
  -e EMAIL_USER=petitions@example.com \
  -e EMAIL_PASSWORD=... \
  -e USER_FIRST_NAME=Jane \
  -e USER_LAST_NAME=Doe \
  -e USER_EMAIL=janedoe@example.com \
  -e USER_ZIP_CODE=12345 \
  -v petition-data:/app/data \
  persistent-petitioner
```

See main README for env vars and Gmail setup.
