#!/usr/bin/env bash
# Fast post-deploy sanity check (~5 s). Exit code != 0 on any failure.
#   tests/smoke/smoke.sh            (defaults match docker-compose.yml)
set -uo pipefail

API=${BASE_URL:-http://localhost:8085}
WEB=${FRONTEND_URL:-http://localhost:8080}
GRAFANA=${GRAFANA_URL:-http://localhost:3000}
KIBANA=${KIBANA_URL:-http://localhost:5601}
MIMIR=${MIMIR_URL:-http://localhost:9009}
EMAIL=${ADMIN_EMAIL:-admin@example.com}
PASS=${ADMIN_PASSWORD:-password123}

fail=0
check() {  # name, command...
  local name=$1; shift
  if "$@" >/dev/null 2>&1; then printf '  \033[32mPASS\033[0m  %s\n' "$name"
  else printf '  \033[31mFAIL\033[0m  %s\n' "$name"; fail=1; fi
}
http_ok() { curl -fsS -m 10 -o /dev/null "$1"; }

echo "== application"
check "backend liveness"          http_ok "$API/health"
check "backend readiness (DB)"    http_ok "$API/health/ready"
check "frontend serves SPA"       bash -c "curl -fsS -m 10 $WEB/ | grep -q 'id=\"root\"'"
check "frontend proxies /api"     http_ok "$WEB/api/health"
check "anonymous /todos => 401"   bash -c "[ \"\$(curl -s -o /dev/null -w '%{http_code}' $API/todos/)\" = 401 ]"

TOKEN=$(curl -fsS -m 10 -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}" "$API/auth/login" 2>/dev/null \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["data"]["access_token"])' 2>/dev/null)
check "admin login returns token" test -n "$TOKEN"
check "authenticated /todos/"      curl -fsS -m 10 -H "Authorization: Bearer $TOKEN" "$API/todos"

echo "== observability"
check "grafana healthy"           http_ok "$GRAFANA/api/health"
check "kibana reachable"          bash -c "curl -s -m 10 -o /dev/null -w '%{http_code}' $KIBANA/api/status | grep -qE '^(200|401)$'"
check "mimir ready"               http_ok "$MIMIR/ready"

[ $fail -eq 0 ] && echo "SMOKE OK" || { echo "SMOKE FAILED"; exit 1; }
