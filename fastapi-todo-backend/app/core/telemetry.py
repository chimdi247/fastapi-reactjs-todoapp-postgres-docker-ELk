"""Manual OpenTelemetry instrumentation (API only).

Auto-instrumentation (FastAPI, SQLAlchemy, logging, providers and exporters) is
done by the `opentelemetry-instrument` launcher, configured through OTEL_*
environment variables - see docker-compose.yml and observability/otel-collector.

This module only uses the OpenTelemetry *API*. When no SDK is configured (unit
tests, plain `uvicorn` in local dev) every call below is a harmless no-op.

Business KPI metrics exposed (Prometheus names after the collector/Mimir hop):
  todos_created_total / todos_updated_total / todos_completed_total /
  todos_deleted_total, auth_logins_total{outcome}, todos_current{state},
  app_uptime_seconds, app_info
"""

import time
from typing import Iterable

from opentelemetry import metrics, trace
from opentelemetry.metrics import CallbackOptions, Observation

from app.core.config import settings

_START = time.monotonic()

tracer = trace.get_tracer("todo.app", settings.SERVICE_VERSION)
_meter = metrics.get_meter("todo.app", settings.SERVICE_VERSION)

# --- Business counters -----------------------------------------------------
todos_created = _meter.create_counter(
    "todos.created", unit="1", description="Todos created"
)
todos_updated = _meter.create_counter(
    "todos.updated", unit="1", description="Todos updated"
)
todos_completed = _meter.create_counter(
    "todos.completed", unit="1", description="Todos transitioned to completed"
)
todos_deleted = _meter.create_counter(
    "todos.deleted", unit="1", description="Todos deleted"
)
auth_logins = _meter.create_counter(
    "auth.logins", unit="1", description="Login attempts by outcome"
)

# --- Gauges (state sampled from the DB by a background task) ---------------
_todo_state: dict[str, int] = {"open": 0, "completed": 0}


def set_todo_state(open_count: int, completed_count: int) -> None:
    _todo_state["open"] = open_count
    _todo_state["completed"] = completed_count


def _observe_todos(_: CallbackOptions) -> Iterable[Observation]:
    for state, value in _todo_state.items():
        yield Observation(value, {"state": state})


def _observe_uptime(_: CallbackOptions) -> Iterable[Observation]:
    yield Observation(time.monotonic() - _START)


def _observe_info(_: CallbackOptions) -> Iterable[Observation]:
    yield Observation(
        1,
        {"version": settings.SERVICE_VERSION, "environment": settings.ENVIRONMENT},
    )


_meter.create_observable_gauge(
    "todos.current", callbacks=[_observe_todos], description="Todos by state"
)
_meter.create_observable_gauge(
    "app.uptime",
    callbacks=[_observe_uptime],
    unit="s",
    description="Seconds since the process started",
)
_meter.create_observable_gauge(
    "app.info", callbacks=[_observe_info], description="Static build info (always 1)"
)
