# Install the Python dependencies first so later code edits build faster.
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential default-libmysqlclient-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# The final image only needs the packages and MariaDB client library.
FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    DJANGO_DEBUG=False SQLITE_PATH=/app/data/db.sqlite3
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb3 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home appuser \
    && mkdir -p /app/data /app/staticfiles \
    && chown -R appuser:appuser /app
COPY --from=builder /install /usr/local
WORKDIR /app
COPY --chown=appuser:appuser . .
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/', timeout=3)" || exit 1
CMD ["sh", "docker-entrypoint.sh"]
