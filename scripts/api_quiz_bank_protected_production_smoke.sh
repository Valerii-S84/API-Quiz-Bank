#!/usr/bin/env sh
set -eu

BASE_URL="${API_QUIZ_BANK_BASE_URL:-http://127.0.0.1:8010}"
EXPECTED_PUBLISHED_ITEMS="${API_QUIZ_BANK_EXPECTED_PUBLISHED_ITEMS:-30974}"
EXPECTED_ACTIVE_SOURCES="${API_QUIZ_BANK_EXPECTED_ACTIVE_SOURCES:-116}"
POSTGRES_CONTAINER="${API_QUIZ_BANK_POSTGRES_CONTAINER:-api-quiz-bank-postgres}"
POSTGRES_DB="${API_QUIZ_BANK_POSTGRES_DB:-api_quiz_bank}"
POSTGRES_USER="${API_QUIZ_BANK_POSTGRES_USER:-api_quiz_bank}"
POSTGRES_PASSWORD="${API_QUIZ_BANK_POSTGRES_PASSWORD:?set API_QUIZ_BANK_POSTGRES_PASSWORD}"
REPORT_PATH="${API_QUIZ_BANK_PROTECTED_SMOKE_REPORT_PATH:-}"

SMOKE_CONSUMER_ID="${API_QUIZ_BANK_SMOKE_CONSUMER_ID:-production_corpus_smoke}"
SMOKE_API_KEY="${API_QUIZ_BANK_SMOKE_API_KEY:-}"
SMOKE_API_KEY_FILE="${API_QUIZ_BANK_SMOKE_API_KEY_FILE:-/root/api-quiz-bank/production-corpus-smoke-api-key}"
QUOTA_CONSUMER_ID="${API_QUIZ_BANK_QUOTA_CONSUMER_ID:-production_corpus_quota_blocked}"
QUOTA_API_KEY="${API_QUIZ_BANK_QUOTA_API_KEY:-}"
QUOTA_API_KEY_FILE="${API_QUIZ_BANK_QUOTA_API_KEY_FILE:-/root/api-quiz-bank/production-corpus-quota-blocked-api-key}"
NO_ENTITLEMENT_CONSUMER_ID="${API_QUIZ_BANK_NO_ENTITLEMENT_CONSUMER_ID:-consumer_no_entitlement}"
NO_ENTITLEMENT_API_KEY="${API_QUIZ_BANK_NO_ENTITLEMENT_API_KEY:-}"
NO_ENTITLEMENT_API_KEY_FILE="${API_QUIZ_BANK_NO_ENTITLEMENT_API_KEY_FILE:-/root/api-quiz-bank/consumer-no-entitlement-api-key}"

read_secret_value() {
  label="$1"
  env_value="$2"
  file_path="$3"
  if [ -n "$env_value" ]; then
    printf '%s' "$env_value"
    return 0
  fi
  if [ -r "$file_path" ]; then
    awk 'NR == 1 {printf "%s", $0}' "$file_path"
    return 0
  fi
  echo "$label missing: set the environment variable or readable key file" >&2
  exit 1
}

SMOKE_API_KEY="$(read_secret_value "smoke API key" "$SMOKE_API_KEY" "$SMOKE_API_KEY_FILE")"
QUOTA_API_KEY="$(read_secret_value "quota smoke API key" "$QUOTA_API_KEY" "$QUOTA_API_KEY_FILE")"
NO_ENTITLEMENT_API_KEY="$(
  read_secret_value \
    "no-entitlement smoke API key" \
    "$NO_ENTITLEMENT_API_KEY" \
    "$NO_ENTITLEMENT_API_KEY_FILE"
)"

query_scalar() {
  docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" "$POSTGRES_CONTAINER" \
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -A -c "$1"
}

published_items="$(query_scalar "SELECT COUNT(*) FROM quiz_items WHERE status = 'published';")"
active_sources="$(query_scalar "SELECT COUNT(*) FROM sources WHERE status = 'active';")"
status_counts="$(docker exec -e PGPASSWORD="$POSTGRES_PASSWORD" "$POSTGRES_CONTAINER" \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -A -F ':' \
  -c "SELECT status, COUNT(*) FROM quiz_items GROUP BY status ORDER BY status;" | paste -sd ',' -)"

tmp_report="$(mktemp)"
python3 - \
  "$BASE_URL" \
  "$EXPECTED_PUBLISHED_ITEMS" \
  "$EXPECTED_ACTIVE_SOURCES" \
  "$published_items" \
  "$active_sources" \
  "$status_counts" \
  "$SMOKE_CONSUMER_ID" \
  "$SMOKE_API_KEY" \
  "$QUOTA_CONSUMER_ID" \
  "$QUOTA_API_KEY" \
  "$NO_ENTITLEMENT_CONSUMER_ID" \
  "$NO_ENTITLEMENT_API_KEY" >"$tmp_report" <<'PY'
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime

base_url = sys.argv[1].rstrip("/")
expected_published_items = int(sys.argv[2])
expected_active_sources = int(sys.argv[3])
published_items = int(sys.argv[4])
active_sources = int(sys.argv[5])
status_counts = sys.argv[6]
smoke_consumer_id = sys.argv[7]
smoke_api_key = sys.argv[8]
quota_consumer_id = sys.argv[9]
quota_api_key = sys.argv[10]
no_entitlement_consumer_id = sys.argv[11]
no_entitlement_api_key = sys.argv[12]


def request(path, method="GET", payload=None, headers=None):
    body = None
    request_headers = headers or {}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        request_headers = {"Content-Type": "application/json", **request_headers}
    req = urllib.request.Request(
        f"{base_url}{path}",
        data=body,
        headers=request_headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        content = error.read().decode("utf-8")
        try:
            return error.code, json.loads(content)
        except json.JSONDecodeError:
            return error.code, {"raw": content}


def next_item(consumer_id, api_key):
    return request(
        "/v1/quiz-items/next",
        method="POST",
        payload={"consumer_id": consumer_id},
        headers={
            "X-Consumer-Id": consumer_id,
            "X-QuizBank-API-Key": api_key,
        },
    )


health_status, health = request("/health")
ready_status, ready = request("/ready")
no_key_status, no_key = request(
    "/v1/quiz-items/next",
    method="POST",
    payload={"consumer_id": smoke_consumer_id},
)
first_status, first = next_item(smoke_consumer_id, smoke_api_key)
if first_status == 200:
    first_item_id = first["quiz_item"]["id"]
    delivery_id = first["delivery_id"]
    selected_item_status = first["delivery"]["item_status"]
else:
    first_item_id = None
    delivery_id = "missing"
    selected_item_status = None
delivery_status, delivery = request(
    f"/v1/deliveries/{delivery_id}",
    headers={
        "X-Consumer-Id": smoke_consumer_id,
        "X-QuizBank-API-Key": smoke_api_key,
    },
)
second_status, second = next_item(smoke_consumer_id, smoke_api_key)
quota_status, quota = next_item(quota_consumer_id, quota_api_key)
cross_status, cross = request(
    f"/v1/deliveries/{delivery_id}",
    headers={
        "X-Consumer-Id": quota_consumer_id,
        "X-QuizBank-API-Key": quota_api_key,
    },
)
entitlement_status, entitlement = request(
    "/v1/quiz-items/next",
    method="POST",
    payload={
        "consumer_id": no_entitlement_consumer_id,
        "cefr_level": "A2",
        "theme_ids": ["T10"],
    },
    headers={
        "X-Consumer-Id": no_entitlement_consumer_id,
        "X-QuizBank-API-Key": no_entitlement_api_key,
    },
)
repeat_repeated_same_item = bool(
    second_status == 200 and first_item_id is not None and second["quiz_item"]["id"] == first_item_id
)
checks = {
    "published_items": published_items,
    "active_sources": active_sources,
    "status_counts": status_counts,
    "health_status": health_status,
    "ready_status": ready_status,
    "no_key_status": no_key_status,
    "next_item_status": first_status,
    "selected_item_id": first_item_id,
    "selected_item_status": selected_item_status,
    "language_code": first.get("language_code"),
    "content_bank_id": first.get("content_bank_id"),
    "bank_version_id": first.get("bank_version_id"),
    "quiz_item_language_code": first.get("quiz_item", {}).get("language_code"),
    "selection_language_code": first.get("selection", {}).get("decision", {}).get("language_code"),
    "delivery_read_status": delivery_status,
    "repeat_control_status": second_status,
    "repeat_control_repeated_same_item": repeat_repeated_same_item,
    "quota_status": quota_status,
    "quota_reason_code": quota.get("reason_code"),
    "cross_consumer_delivery_status": cross_status,
    "cross_consumer_reason_code": cross.get("reason_code"),
    "entitlement_status": entitlement_status,
    "entitlement_reason_code": entitlement.get("reason_code"),
}
ok = (
    published_items == expected_published_items
    and active_sources == expected_active_sources
    and health_status == 200
    and health.get("status") == "ok"
    and ready_status == 200
    and ready.get("status") == "ok"
    and no_key_status == 401
    and first_status == 200
    and selected_item_status == "published"
    and first.get("language_code") == "de"
    and first.get("content_bank_id") == "german-core"
    and first.get("bank_version_id") == "german-core:2026-06-12-baseline"
    and first.get("quiz_item", {}).get("language_code") == "de"
    and first.get("selection", {}).get("decision", {}).get("language_code") == "de"
    and delivery_status == 200
    and second_status == 200
    and repeat_repeated_same_item is False
    and quota_status == 429
    and quota.get("reason_code") == "QUOTA_EXCEEDED"
    and cross_status in {403, 404}
    and entitlement_status == 403
    and entitlement.get("reason_code") == "ENTITLEMENT_MISSING_FEATURE"
)
report = {
    "report_type": "protected_production_smoke",
    "executed_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    "expected_published_items": expected_published_items,
    "expected_active_sources": expected_active_sources,
    "checks": checks,
    "decision": "protected_production_smoke_ok" if ok else "protected_production_smoke_failed",
}
print(json.dumps(report, ensure_ascii=False, sort_keys=True))
if not ok:
    raise SystemExit(1)
PY

if [ -n "$REPORT_PATH" ]; then
  mkdir -p "$(dirname "$REPORT_PATH")"
  cp "$tmp_report" "$REPORT_PATH"
fi
cat "$tmp_report"
rm -f "$tmp_report"
