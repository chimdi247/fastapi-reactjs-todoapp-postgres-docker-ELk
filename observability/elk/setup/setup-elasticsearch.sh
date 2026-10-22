#!/usr/bin/env bash
# One-shot job: prepares Elasticsearch for logs + traces. Idempotent (all PUTs).
#   1. sets the kibana_system password
#   2. ILM policy (rollover + retention)
#   3. data-stream index templates for logs-todo-* and traces-todo-*
#   4. S3 snapshot repository (the "log storage bucket") + SLM schedule
set -euo pipefail

ES="http://elasticsearch:9200"
AUTH=(-u "elastic:${ELASTIC_PASSWORD}")
JSON=(-H "Content-Type: application/json")

call() {  # call METHOD PATH [BODY]  -> fails loudly on non-2xx
  local method=$1 path=$2 body=${3:-}
  local args=(-sS -o /tmp/resp -w '%{http_code}' "${AUTH[@]}" "${JSON[@]}" -X "$method" "$ES$path")
  [[ -n "$body" ]] && args+=(-d "$body")
  local code; code=$(curl "${args[@]}")
  if [[ "$code" != 2* ]]; then echo "FAILED $method $path -> $code"; cat /tmp/resp; echo; exit 1; fi
  echo "ok  $method $path ($code)"
}

echo "waiting for Elasticsearch..."
until curl -sf "${AUTH[@]}" "$ES/_cluster/health?wait_for_status=yellow&timeout=5s" >/dev/null; do sleep 3; done

call POST "/_security/user/kibana_system/_password" "{\"password\":\"${KIBANA_SYSTEM_PASSWORD}\"}"

DIR=/setup
call PUT "/_ilm/policy/todo-observability" "$(cat $DIR/ilm-policy.json)"
call PUT "/_index_template/logs-todo"      "$(cat $DIR/template-logs.json)"
call PUT "/_index_template/traces-todo"    "$(cat $DIR/template-traces.json)"

# --- S3 snapshot repository (verifies bucket access on creation) ---
call PUT "/_snapshot/${ES_SNAPSHOT_REPO}" "{
  \"type\": \"s3\",
  \"settings\": { \"bucket\": \"${ES_SNAPSHOT_BUCKET}\", \"client\": \"default\", \"base_path\": \"todo-observability\" }
}"

# --- SLM: scheduled snapshots of logs+traces into the bucket, 30 d retention ---
call PUT "/_slm/policy/todo-logs-to-s3" "{
  \"schedule\": \"${ES_SNAPSHOT_CRON}\",
  \"name\": \"<todo-logs-{now/d}>\",
  \"repository\": \"${ES_SNAPSHOT_REPO}\",
  \"config\": { \"indices\": [\"logs-todo-*\", \"traces-todo-*\"], \"include_global_state\": false, \"ignore_unavailable\": true },
  \"retention\": { \"expire_after\": \"30d\", \"min_count\": 3, \"max_count\": 200 }
}"

echo "elasticsearch setup complete"
