"""Structured (JSON) logging with OpenTelemetry trace correlation.

Two sinks, both fed from the root logger:
  * stdout  - one JSON object per line (what `docker logs` shows)
  * OTLP    - attached automatically by `opentelemetry-instrument`
              (OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true) and
              shipped through the collector to Elasticsearch / Kibana.
"""

import json
import logging
import sys
from datetime import datetime, timezone

from opentelemetry import trace

from app.core.config import settings

# Attributes every LogRecord has; anything else came from `extra={...}`.
_STANDARD_ATTRS = frozenset(
    logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys()
) | {"message", "asctime", "taskName"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        span_ctx = trace.get_current_span().get_span_context()
        payload: dict[str, object] = {
            "@timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service.name": settings.SERVICE_NAME,
            "service.version": settings.SERVICE_VERSION,
            "deployment.environment": settings.ENVIRONMENT,
        }
        if span_ctx.is_valid:
            payload["trace_id"] = format(span_ctx.trace_id, "032x")
            payload["span_id"] = format(span_ctx.span_id, "016x")
        for key, value in record.__dict__.items():
            if key not in _STANDARD_ATTRS and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, ensure_ascii=False)


def configure_logging() -> None:
    """Idempotent. Safe to call once at import time of the app."""
    root = logging.getLogger()
    root.setLevel(settings.LOG_LEVEL.upper())

    if not any(getattr(h, "_todo_json", False) for h in root.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        handler._todo_json = True  # type: ignore[attr-defined]
        root.addHandler(handler)

    # Route uvicorn's own loggers through the root logger so they are JSON on
    # stdout *and* exported over OTLP. Request logs come from our middleware.
    for name in ("uvicorn", "uvicorn.error"):
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.propagate = True
    logging.getLogger("uvicorn.access").disabled = True
