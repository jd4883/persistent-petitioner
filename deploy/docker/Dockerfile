# Use official Playwright image — includes Chromium and system deps for petition signing.
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble AS builder

ENV LANG=C.UTF-8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/venv/bin:$PATH"

WORKDIR /app

RUN python -m venv /app/venv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p data && chown -R pwuser:pwuser /app

FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

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

USER pwuser

EXPOSE 8080

CMD ["python", "main.py", "serve", "--host", "0.0.0.0", "--port", "8080"]
