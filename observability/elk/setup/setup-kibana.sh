#!/usr/bin/env bash
# One-shot job: creates the Kibana data views so logs/traces are searchable the
# first time you open Discover. Idempotent (`override: true`).
set -euo pipefail

KB="http://kibana:5601"
AUTH=(-u "elastic:${ELASTIC_PASSWORD}")
HDR=(-H "kbn-xsrf: true" -H "Content-Type: application/json")

echo "waiting for Kibana..."
until curl -sf "${AUTH[@]}" "$KB/api/status" | grep -q '"level":"available"'; do sleep 5; done

create_view() {  # id title name
  curl -sSf "${AUTH[@]}" "${HDR[@]}" -X POST "$KB/api/data_views/data_view" -d "{
    \"override\": true,
    \"data_view\": { \"id\": \"$1\", \"title\": \"$2\", \"name\": \"$3\", \"timeFieldName\": \"@timestamp\" }
  }" >/dev/null
  echo "ok  data view: $3 ($2)"
}

create_view todo-logs   "logs-todo-*"   "Todo App - Logs"
create_view todo-traces "traces-todo-*" "Todo App - Traces"

curl -sSf "${AUTH[@]}" "${HDR[@]}" -X POST "$KB/api/data_views/default" \
  -d '{"data_view_id":"todo-logs","force":true}' >/dev/null
echo "kibana setup complete"
