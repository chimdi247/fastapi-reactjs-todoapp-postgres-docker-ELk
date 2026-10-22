# syntax=docker/dockerfile:1.7

# ---------- builder: resolve + install deps into an isolated venv ----------
FROM python:3.14-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build
COPY requirements.txt .
RUN pip install -r requirements.txt


# ---------- runtime: small, non-root ----------
FROM python:3.14-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

RUN groupadd --system --gid 10001 app \
 && useradd  --system --uid 10001 --gid app --home-dir /app --shell /usr/sbin/nologin app

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app app ./app
COPY --chown=app:app migrations ./migrations
COPY --chown=app:app alembic.ini ./alembic.ini

USER app
EXPOSE 8085

HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=5 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8085/health', timeout=2).status == 200 else 1)"

# `opentelemetry-instrument` wraps the process and auto-instruments FastAPI,
# SQLAlchemy and logging; exporters/endpoints come from the OTEL_* env vars set
# in docker-compose.yml. If OTEL_* is unset it simply exports nothing useful, so
# the image still runs standalone.
CMD ["opentelemetry-instrument", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", "--port", "8085", \
     "--no-access-log", "--proxy-headers", "--forwarded-allow-ips", "*"]
