"""Proves telemetry really flows end to end:

  backend --OTLP--> collector --> Mimir (S3)     [metrics]  --> Grafana
                              --> Elasticsearch  [logs, traces] --> Kibana
Slow by nature (batching + scrape intervals): each check polls up to ~2 minutes.
"""
import os
import secrets
import time

import httpx
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.observability]

MIMIR = os.getenv("MIMIR_URL", "http://localhost:9009")
ES = os.getenv("ES_URL", "http://localhost:9200")
ES_AUTH = ("elastic", os.getenv("ELASTIC_PASSWORD", "change_me_elastic"))
GRAFANA = os.getenv("GRAFANA_URL", "http://localhost:3000")
GRAFANA_AUTH = (os.getenv("GRAFANA_ADMIN_USER", "admin"), os.getenv("GRAFANA_ADMIN_PASSWORD", "change_me_grafana"))
KIBANA = os.getenv("KIBANA_URL", "http://localhost:5601")
MAILPIT = os.getenv("MAILPIT_URL", "http://localhost:8025")


def eventually(fn, timeout=150, interval=5, msg="condition"):
    deadline, last = time.time() + timeout, None
    while time.time() < deadline:
        try:
            last = fn()
            if last:
                return last
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as e:
            last = e
        time.sleep(interval)
    pytest.fail(f"timed out waiting for {msg} (last: {last!r})")


def prom(query):
    r = httpx.get(f"{MIMIR}/prometheus/api/v1/query", params={"query": query}, timeout=10)
    r.raise_for_status()
    return r.json()["data"]["result"]


@pytest.fixture(scope="module", autouse=True)
def generate_traffic(api, todo, anon):
    for _ in range(5):
        todo()
        api.get("/todos")
    anon.post("/auth/login", json={"email": "admin@example.com", "password": "definitely-wrong"})  # a failed login KPI


def test_http_metrics_reach_mimir():
    eventually(lambda: prom('http_server_request_duration_seconds_count{job="todo-backend"}'),
               msg="HTTP server metrics in Mimir")


def test_business_kpi_metrics_reach_mimir():
    eventually(lambda: prom('todos_created_total{job="todo-backend"}'), msg="todos_created_total")
    eventually(lambda: prom('auth_logins_total{job="todo-backend",outcome="failure"}'), msg="failed-login counter")
    eventually(lambda: prom('todos_current{job="todo-backend"}'), msg="todos_current gauge")


def test_container_and_node_metrics_reach_mimir():
    eventually(lambda: prom('container_memory_working_set_bytes{name="todo-backend"}'), msg="cAdvisor metrics")
    eventually(lambda: prom('container_spec_memory_limit_bytes{name="todo-backend"} > 0'), msg="memory limit metric")
    eventually(lambda: prom("node_memory_MemAvailable_bytes"), msg="node-exporter metrics")


def test_uptime_probe_reports_backend_up():
    res = eventually(lambda: prom('httpcheck_status{http_status_class="2xx",http_url=~".*backend.*"}'), msg="httpcheck")
    assert float(res[0]["value"][1]) == 1.0


def test_structured_logs_reach_elasticsearch_with_trace_ids():
    def has_logs():
        r = httpx.post(f"{ES}/logs-todo-*/_search", auth=ES_AUTH, timeout=10,
                       json={"size": 1, "query": {"match_phrase": {"message": "todo created"}}})
        r.raise_for_status()
        return r.json()["hits"]["hits"]
    hits = eventually(has_logs, msg="'todo created' log in Elasticsearch")
    src = hits[0]["_source"]
    assert src.get("service", {}).get("name") == "todo-backend" or src.get("service.name") == "todo-backend"


def test_trace_context_propagates_from_request_to_elasticsearch(api):
    trace_id = secrets.token_hex(16)
    r = api.get("/todos", headers={"traceparent": f"00-{trace_id}-{secrets.token_hex(8)}-01"})
    assert r.status_code == 200

    def found():
        res = httpx.post(f"{ES}/traces-todo-*/_search", auth=ES_AUTH, timeout=10,
                         json={"size": 1, "query": {"query_string": {"query": f'"{trace_id}"'}}})
        res.raise_for_status()
        return res.json()["hits"]["total"]["value"] > 0
    eventually(found, msg=f"trace {trace_id} in Elasticsearch")


def test_elasticsearch_snapshot_repository_points_at_s3():
    r = httpx.get(f"{ES}/_snapshot/s3-logs-archive", auth=ES_AUTH, timeout=10)
    assert r.status_code == 200
    assert r.json()["s3-logs-archive"]["type"] == "s3"
    assert httpx.get(f"{ES}/_slm/policy/todo-logs-to-s3", auth=ES_AUTH, timeout=10).status_code == 200


def test_grafana_datasources_and_dashboard_are_provisioned():
    ds = {d["uid"]: d for d in httpx.get(f"{GRAFANA}/api/datasources", auth=GRAFANA_AUTH, timeout=10).json()}
    assert ds["mimir"]["type"] == "prometheus" and ds["mimir"]["isDefault"] is True
    assert "es-logs" in ds
    found = httpx.get(f"{GRAFANA}/api/search", params={"query": "Todo App"}, auth=GRAFANA_AUTH, timeout=10).json()
    assert any(d.get("uid") == "todo-app-overview" for d in found)


def test_grafana_can_query_mimir():
    r = httpx.get(f"{GRAFANA}/api/datasources/proxy/uid/mimir/api/v1/query", params={"query": "up"},
                  auth=GRAFANA_AUTH, timeout=10)
    assert r.status_code == 200 and r.json()["status"] == "success"


def test_grafana_alert_rules_and_email_contact_point_provisioned():
    rules = httpx.get(f"{GRAFANA}/api/v1/provisioning/alert-rules", auth=GRAFANA_AUTH, timeout=10).json()
    titles = {r["title"] for r in rules}
    assert {"Container CPU above threshold", "Container memory above threshold",
            "Node CPU above threshold", "Node memory above threshold"} <= titles
    cpu = next(r for r in rules if r["uid"] == "container-cpu-high")
    thr = next(d for d in cpu["data"] if d["refId"] == "C")["model"]["conditions"][0]["evaluator"]["params"][0]
    assert float(thr) == float(os.getenv("ALERT_CPU_THRESHOLD", "40"))
    cps = httpx.get(f"{GRAFANA}/api/v1/provisioning/contact-points", auth=GRAFANA_AUTH, timeout=10).json()
    assert any(c["type"] == "email" for c in cps)


def test_kibana_data_views_exist():
    def views():
        r = httpx.get(f"{KIBANA}/api/data_views", auth=ES_AUTH, headers={"kbn-xsrf": "true"}, timeout=10)
        r.raise_for_status()
        return {v["id"] for v in r.json()["data_view"]}
    assert {"todo-logs", "todo-traces"} <= eventually(views, msg="Kibana data views")


def test_mailpit_smtp_sink_is_up():
    assert httpx.get(f"{MAILPIT}/api/v1/info", timeout=10).status_code == 200
