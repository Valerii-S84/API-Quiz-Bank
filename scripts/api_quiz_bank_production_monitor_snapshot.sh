#!/usr/bin/env sh
set -eu

BASE_URL="${API_QUIZ_BANK_BASE_URL:-https://api.valerchik.de}"
PUBLIC_API_KEY_FILE="${API_QUIZ_BANK_PUBLIC_API_KEY_FILE:-/root/api-quiz-bank/public-api-key}"
REPORT_DIR="${API_QUIZ_BANK_MONITOR_REPORT_DIR:-/var/log/api-quiz-bank/monitoring}"
API_CONTAINER="${API_QUIZ_BANK_API_CONTAINER:-api-quiz-bank-pilot}"
POSTGRES_CONTAINER="${API_QUIZ_BANK_POSTGRES_CONTAINER:-api-quiz-bank-postgres}"
BACKUP_TIMER="${API_QUIZ_BANK_BACKUP_TIMER:-api-quiz-bank-postgres-backup.timer}"

mkdir -p "$REPORT_DIR"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
report_path="$REPORT_DIR/production_monitor_$timestamp.md"

if [ -n "${API_QUIZ_BANK_PUBLIC_API_KEY:-}" ]; then
  public_api_key="$API_QUIZ_BANK_PUBLIC_API_KEY"
elif [ -r "$PUBLIC_API_KEY_FILE" ]; then
  public_api_key="$(cat "$PUBLIC_API_KEY_FILE")"
else
  public_api_key=""
fi

http_code() {
  curl -sS -o /tmp/api_quiz_bank_monitor_body.out -w "%{http_code}" "$@"
}

health_no_key="$(http_code "$BASE_URL/health" || true)"
health_with_key="skipped"
ready_with_key="skipped"
delivery_no_key="skipped"

if [ -n "$public_api_key" ]; then
  health_with_key="$(http_code -H "X-API-Key: $public_api_key" "$BASE_URL/health" || true)"
  ready_with_key="$(http_code -H "X-API-Key: $public_api_key" "$BASE_URL/ready" || true)"
  delivery_no_key="$(http_code \
    -X POST "$BASE_URL/v1/quiz-items/next" \
    -H "Content-Type: application/json" \
    -d '{"consumer_id":"consumer_no_entitlement","cefr_level":"A2","theme_ids":["T10"]}' || true)"
fi

api_state="unavailable"
postgres_state="unavailable"
if command -v docker >/dev/null 2>&1; then
  api_state="$(docker inspect -f '{{.State.Status}}/{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' "$API_CONTAINER" 2>/dev/null || true)"
  postgres_state="$(docker inspect -f '{{.State.Status}}/{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' "$POSTGRES_CONTAINER" 2>/dev/null || true)"
fi

backup_timer_state="unavailable"
backup_service_result="unavailable"
if command -v systemctl >/dev/null 2>&1; then
  backup_timer_state="$(systemctl is-active "$BACKUP_TIMER" 2>/dev/null || true)"
  backup_service_result="$(systemctl show "${BACKUP_TIMER%.timer}.service" -p Result -p ExecMainStatus --value 2>/dev/null | paste -sd / - || true)"
fi

status="ok"
[ "$health_no_key" = "401" ] || status="fail"
if [ -n "$public_api_key" ]; then
  [ "$health_with_key" = "200" ] || status="fail"
  [ "$ready_with_key" = "200" ] || status="fail"
  [ "$delivery_no_key" = "401" ] || status="fail"
else
  status="fail"
fi
[ "$api_state" = "running/healthy" ] || status="fail"
[ "$postgres_state" = "running/healthy" ] || status="fail"
[ "$backup_timer_state" = "active" ] || status="fail"

cat >"$report_path" <<EOF
# API Quiz Bank Production Monitor Snapshot

Generated: $timestamp
Base URL: $BASE_URL
Status: $status

| Check | Result |
|---|---|
| Public health without edge key | $health_no_key |
| Public health with edge key | $health_with_key |
| Public ready with edge key | $ready_with_key |
| Public delivery without edge key | $delivery_no_key |
| API container | $api_state |
| PostgreSQL container | $postgres_state |
| PostgreSQL backup timer | $backup_timer_state |
| Latest PostgreSQL backup service result | $backup_service_result |

Secrets are not written to this report.
EOF

if [ "$status" != "ok" ]; then
  echo "production-monitor-snapshot-failed $report_path" >&2
  exit 1
fi

echo "production-monitor-snapshot-ok $report_path"
