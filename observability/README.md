# Observability

```
 browser ──OTLP/HTTP (via nginx /otlp)─┐
 FastAPI ──OTLP/gRPC──────────────────┤
 cAdvisor / node-exporter / nginx /    │      ┌────────────► Mimir ──► S3 (MinIO)  ──► Grafana (dashboard + alerts ─► SMTP)
 PostgreSQL / uptime probes ──scrape───┴─► OpenTelemetry ────┤
                                          Collector          └────────────► Elasticsearch ──► Kibana
                                                                            (logs-todo-*, traces-todo-*)
                                                                             └─ hourly snapshots ─► S3 (MinIO) bucket
```

| Folder | What |
|---|---|
| `otel-collector/config.yaml` | receivers (OTLP, cAdvisor, node-exporter, httpcheck, nginx, postgresql), pipelines, exporters |
| `mimir/mimir.yaml` | monolithic Mimir; TSDB blocks / ruler / alertmanager data in S3 buckets |
| `minio/create-buckets.sh` | creates the buckets (local S3) |
| `elk/` | `elasticsearch.yml` + keystore entrypoint (S3 creds), `setup/` (ILM, templates, S3 snapshot repo + SLM, Kibana data views), `kibana.yml` |
| `grafana/` | `grafana.ini` (SMTP), provisioning (datasources, dashboards, alert rules, contact point, policy), `dashboards/todo-app-overview.json` |

## Where the log "bucket" is
Elasticsearch keeps hot data on its volume (14 d ILM) and an SLM policy snapshots `logs-todo-*` /
`traces-todo-*` **to the S3 bucket `es-log-archive`** every hour (`ES_SNAPSHOT_CRON`), kept 30 d.
Metrics are stored by Mimir **directly in S3** (`mimir-blocks`), with only the WAL on local disk.

## Use real AWS S3 instead of MinIO
* `mimir.yaml`: remove `endpoint` / `insecure`, set `region`, credentials (or an IAM role).
* `elasticsearch.yml`: remove `endpoint`, `protocol`, `path_style_access`; set `s3.client.default.region`.
* Create the four buckets yourself and drop `minio` / `minio-init` from compose.

## Alerts
Grafana-managed rules (folder *Todo App Alerts*): container & node CPU > 40 %, container & node memory > 40 %
(`ALERT_CPU_THRESHOLD` / `ALERT_MEMORY_THRESHOLD`), backend down, 5xx ratio > 5 %, p95 > 500 ms.
Mail goes through the SMTP settings in `.env`; by default to Mailpit (http://localhost:8025).
Container rules cover backend/frontend/db/collector (Elasticsearch/Kibana idle > 40 % of their memory limit by design) -
widen the `name=~` regex in `grafana/provisioning/alerting/alert-rules.yaml` to include them.
Container % is relative to the compose `deploy.resources.limits`, so every service has a limit.

## Dashboard
*Todo App - SLOs, Traffic & Infrastructure*: uptime, availability & latency SLIs vs SLO (99.5 % / 95 % < 250 ms),
error budget & burn rate, RED metrics, successful vs failed request totals, business KPIs, container/node CPU & memory, DB.

## Troubleshooting
* Empty HTTP panels -> check metric names in Mimir (`http_server_request_duration_seconds_count`); they require
  `OTEL_SEMCONV_STABILITY_OPT_IN=http` (set in compose).
* cAdvisor on Docker Desktop (macOS/Windows) reports the Linux VM; node panels show that VM too.
* `docker compose logs es-setup kibana-setup` shows the one-shot setup jobs.
