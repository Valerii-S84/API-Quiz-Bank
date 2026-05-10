#!/usr/bin/env sh
set -eu

BASE_URL="${API_QUIZ_BANK_BASE_URL:-https://api.valerchik.de}"
PUBLIC_API_KEY_FILE="${API_QUIZ_BANK_PUBLIC_API_KEY_FILE:-/root/api-quiz-bank/public-api-key}"
REPORT_DIR="${API_QUIZ_BANK_MONITOR_REPORT_DIR:-/var/log/api-quiz-bank/monitoring}"
API_CONTAINER="${API_QUIZ_BANK_API_CONTAINER:-api-quiz-bank-pilot}"
POSTGRES_CONTAINER="${API_QUIZ_BANK_POSTGRES_CONTAINER:-api-quiz-bank-postgres}"
BACKUP_TIMER="${API_QUIZ_BANK_BACKUP_TIMER:-api-quiz-bank-postgres-backup.timer}"
DISK_CHECK_PATH="${API_QUIZ_BANK_DISK_CHECK_PATH:-$REPORT_DIR}"
DISK_USED_MAX_PERCENT="${API_QUIZ_BANK_DISK_USED_MAX_PERCENT:-90}"
MEMINFO_FILE="${API_QUIZ_BANK_MEMINFO_FILE:-/proc/meminfo}"
MEM_AVAILABLE_MIN_MB="${API_QUIZ_BANK_MEM_AVAILABLE_MIN_MB:-128}"
CONTAINER_RESTART_MAX="${API_QUIZ_BANK_CONTAINER_RESTART_MAX:-0}"
ALERT_WEBHOOK_URL="${API_QUIZ_BANK_ALERT_WEBHOOK_URL:-}"
ALERT_TIMEOUT_SECONDS="${API_QUIZ_BANK_ALERT_TIMEOUT_SECONDS:-10}"

mkdir -p "$REPORT_DIR"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
report_path="$REPORT_DIR/production_monitor_$timestamp.md"
alert_payload_path="$REPORT_DIR/production_monitor_alert_$timestamp.txt"

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

status="ok"
failure_reasons=""
alert_status="disabled"

fail_check() {
  status="fail"
  if [ -n "$failure_reasons" ]; then
    failure_reasons="$failure_reasons; $1"
  else
    failure_reasons="$1"
  fi
}

is_non_negative_integer() {
  case "$1" in
    ''|*[!0-9]*)
      return 1
      ;;
    *)
      return 0
      ;;
  esac
}

send_alert() {
  if [ -z "$ALERT_WEBHOOK_URL" ]; then
    alert_status="disabled"
    return 0
  fi

  cat >"$alert_payload_path" <<EOF
API Quiz Bank production monitor failed
Generated: $timestamp
Report: $report_path
Failures: $failure_reasons
EOF

  if ! command -v curl >/dev/null 2>&1; then
    alert_status="curl-unavailable"
    return 0
  fi

  if curl -fsS --max-time "$ALERT_TIMEOUT_SECONDS" \
    -H "Content-Type: text/plain; charset=utf-8" \
    --data-binary "@$alert_payload_path" \
    "$ALERT_WEBHOOK_URL" >/dev/null 2>&1; then
    alert_status="sent"
  else
    alert_status="failed"
  fi
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
api_restart_count="unavailable"
postgres_restart_count="unavailable"
if command -v docker >/dev/null 2>&1; then
  api_state="$(docker inspect -f '{{.State.Status}}/{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' "$API_CONTAINER" 2>/dev/null || true)"
  postgres_state="$(docker inspect -f '{{.State.Status}}/{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' "$POSTGRES_CONTAINER" 2>/dev/null || true)"
  api_restart_count="$(docker inspect -f '{{.RestartCount}}' "$API_CONTAINER" 2>/dev/null || true)"
  postgres_restart_count="$(docker inspect -f '{{.RestartCount}}' "$POSTGRES_CONTAINER" 2>/dev/null || true)"
fi

backup_timer_state="unavailable"
backup_service_result="unavailable"
if command -v systemctl >/dev/null 2>&1; then
  backup_timer_state="$(systemctl is-active "$BACKUP_TIMER" 2>/dev/null || true)"
  backup_service_result="$(systemctl show "${BACKUP_TIMER%.timer}.service" -p Result -p ExecMainStatus --value 2>/dev/null | paste -sd / - || true)"
fi

disk_used_percent="unavailable"
if command -v df >/dev/null 2>&1; then
  disk_used_raw="$(df -P "$DISK_CHECK_PATH" 2>/dev/null | awk 'NR == 2 {print $5}' || true)"
  disk_used_percent="${disk_used_raw%\%}"
  [ -n "$disk_used_percent" ] || disk_used_percent="unavailable"
fi

mem_available_mb="unavailable"
if [ -r "$MEMINFO_FILE" ]; then
  mem_available_mb="$(awk '/^MemAvailable:/ {printf "%d", $2 / 1024}' "$MEMINFO_FILE" || true)"
  [ -n "$mem_available_mb" ] || mem_available_mb="unavailable"
fi

[ "$health_no_key" = "401" ] || fail_check "public health without edge key expected 401 got $health_no_key"
if [ -n "$public_api_key" ]; then
  [ "$health_with_key" = "200" ] || fail_check "public health with edge key expected 200 got $health_with_key"
  [ "$ready_with_key" = "200" ] || fail_check "public ready with edge key expected 200 got $ready_with_key"
  [ "$delivery_no_key" = "401" ] || fail_check "public delivery without edge key expected 401 got $delivery_no_key"
else
  fail_check "public API key unavailable"
fi
[ "$api_state" = "running/healthy" ] || fail_check "API container expected running/healthy got $api_state"
[ "$postgres_state" = "running/healthy" ] || fail_check "PostgreSQL container expected running/healthy got $postgres_state"
[ "$backup_timer_state" = "active" ] || fail_check "PostgreSQL backup timer expected active got $backup_timer_state"
[ "$backup_service_result" = "success/0" ] || fail_check "latest PostgreSQL backup service expected success/0 got $backup_service_result"

if is_non_negative_integer "$disk_used_percent"; then
  [ "$disk_used_percent" -le "$DISK_USED_MAX_PERCENT" ] || fail_check "disk usage expected <= ${DISK_USED_MAX_PERCENT}% got ${disk_used_percent}%"
else
  fail_check "disk usage unavailable"
fi

if is_non_negative_integer "$mem_available_mb"; then
  [ "$mem_available_mb" -ge "$MEM_AVAILABLE_MIN_MB" ] || fail_check "memory available expected >= ${MEM_AVAILABLE_MIN_MB}MB got ${mem_available_mb}MB"
else
  fail_check "memory available unavailable"
fi

if is_non_negative_integer "$api_restart_count"; then
  [ "$api_restart_count" -le "$CONTAINER_RESTART_MAX" ] || fail_check "API container restarts expected <= $CONTAINER_RESTART_MAX got $api_restart_count"
else
  fail_check "API container restart count unavailable"
fi

if is_non_negative_integer "$postgres_restart_count"; then
  [ "$postgres_restart_count" -le "$CONTAINER_RESTART_MAX" ] || fail_check "PostgreSQL container restarts expected <= $CONTAINER_RESTART_MAX got $postgres_restart_count"
else
  fail_check "PostgreSQL container restart count unavailable"
fi

if [ "$status" != "ok" ]; then
  send_alert
else
  failure_reasons="none"
fi

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
| Disk used percent | $disk_used_percent |
| Memory available MB | $mem_available_mb |
| API container restart count | $api_restart_count |
| PostgreSQL container restart count | $postgres_restart_count |
| Alert notification | $alert_status |
| Failures | $failure_reasons |

Secrets are not written to this report.
EOF

if [ "$status" != "ok" ]; then
  echo "production-monitor-snapshot-failed $report_path" >&2
  exit 1
fi

echo "production-monitor-snapshot-ok $report_path"
