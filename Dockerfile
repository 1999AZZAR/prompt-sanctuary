# syntax=docker/dockerfile:1.7

# ============================================================================
# Stage 1 — base image with system dependencies
# ============================================================================
FROM python:3.12-slim AS base

# Hardening + sane defaults
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # Tell Flask not to trust every proxy by default
    # (override per-deployment if behind a real proxy)
    TRUSTED_PROXY_COUNT=0 \
    # Gunicorn defaults (overridable at `docker run`)
    GUNICORN_WORKERS=2 \
    GUNICORN_THREADS=4 \
    GUNICORN_TIMEOUT=120 \
    PORT=5000

# OS deps: build-essential only needed at pip install time for wheels;
# cleanup in the same layer to keep image small.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        tini \
 && rm -rf /var/lib/apt/lists/*

# Use a non-root user from the start
RUN groupadd --system app && useradd --system --gid app --home /app --shell /sbin/nologin app

WORKDIR /app

# ============================================================================
# Stage 2 — install Python dependencies (cached layer)
# ============================================================================
FROM base AS deps

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Stage 3 — final runtime image
# ============================================================================
FROM base AS runtime

COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# App source
COPY web/ ./web/
COPY migrations/ ./migrations/
COPY alembic.ini ./
COPY devserver.sh ./

# Persistent directories for SQLite + Babel translations
RUN mkdir -p /app/web/database /app/web/database/community /app/web/translations /app/web/backups \
 && chown -R app:app /app

USER app

EXPOSE 5000

# Tini gives us proper signal handling + zombie reaping
ENTRYPOINT ["/usr/bin/tini", "--"]

# Gunicorn for production: 2 workers x 4 threads, 120s timeout (AI calls are slow)
CMD ["sh", "-c", "exec gunicorn \
    --chdir web \
    --bind 0.0.0.0:${PORT} \
    --workers ${GUNICORN_WORKERS} \
    --threads ${GUNICORN_THREADS} \
    --timeout ${GUNICORN_TIMEOUT} \
    --graceful-timeout 30 \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile - \
    app:app"]

# Quick health probe (Gunicorn doesn't expose /health by default,
# but a HEAD on / will return 200/302 fast).
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS -o /dev/null http://127.0.0.1:${PORT}/ || exit 1
