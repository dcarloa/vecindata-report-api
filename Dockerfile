FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app

RUN pip install --no-cache-dir . \
    && playwright install --with-deps chromium

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
