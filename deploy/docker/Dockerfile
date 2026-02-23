FROM cgr.dev/chainguard/python:latest-dev AS builder

ENV LANG=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/venv/bin:$PATH"

WORKDIR /app

RUN python -m venv /app/venv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p data && chown -R 65532:65532 /app

FROM cgr.dev/chainguard/python:latest

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PATH="/app/venv/bin:$PATH"
ENV AUTOMATION_ENABLED=false \
    DATABASE_URL=sqlite:////app/data/persistent_petitioner.db \
    EMAIL_IMAP_HOST= \
    EMAIL_IMAP_PORT=993 \
    EMAIL_USER= \
    EMAIL_PASSWORD= \
    USER_FIRST_NAME= \
    USER_LAST_NAME= \
    USER_EMAIL= \
    USER_ZIP_CODE= \
    USER_PHONE= \
    EMAIL_CHECK_INTERVAL_MINUTES=5 \
    TZ=UTC

COPY --from=builder /app /app

USER 65532:65532

EXPOSE 8080

CMD ["python", "main.py", "serve", "--host", "0.0.0.0", "--port", "8080"]
