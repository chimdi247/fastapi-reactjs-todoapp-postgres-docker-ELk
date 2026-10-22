import json
import logging

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

from app.core.logging import JsonFormatter


def _record(msg="hello", **extra):
    r = logging.LogRecord("app.test", logging.INFO, __file__, 1, msg, (), None)
    for k, v in extra.items():
        setattr(r, k, v)
    return r


@pytest.mark.unit
def test_json_formatter_emits_structured_fields():
    out = json.loads(JsonFormatter().format(_record("todo created", event="todo.created", todo_id=7)))
    assert out["message"] == "todo created"
    assert out["level"] == "INFO" and out["logger"] == "app.test"
    assert out["event"] == "todo.created" and out["todo_id"] == 7
    assert out["service.name"] == "todo-backend"
    assert out["@timestamp"].endswith("Z")
    assert "trace_id" not in out  # no active span


@pytest.mark.unit
def test_json_formatter_correlates_with_active_span():
    tracer = TracerProvider().get_tracer("unit")
    with tracer.start_as_current_span("op") as span:
        out = json.loads(JsonFormatter().format(_record()))
        ctx = span.get_span_context()
    assert out["trace_id"] == format(ctx.trace_id, "032x")
    assert out["span_id"] == format(ctx.span_id, "016x")


@pytest.mark.unit
def test_json_formatter_includes_exception():
    try:
        raise ValueError("boom")
    except ValueError:
        import sys
        r = _record("failed")
        r.exc_info = sys.exc_info()
    out = json.loads(JsonFormatter().format(r))
    assert "ValueError: boom" in out["exception"]


@pytest.mark.unit
def test_manual_metrics_are_safe_noops_without_sdk():
    from app.core import telemetry
    telemetry.todos_created.add(1)
    telemetry.auth_logins.add(1, {"outcome": "success"})
    telemetry.set_todo_state(3, 4)
    assert telemetry._todo_state == {"open": 3, "completed": 4}
    assert trace.get_tracer("x") is not None
