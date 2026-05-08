#!/usr/bin/env sh
set -eu

BASE_URL="${API_QUIZ_BANK_BASE_URL:-http://127.0.0.1:8010}"

python3 - "$BASE_URL" <<'PY'
import json
import sys
import urllib.error
import urllib.request

base_url = sys.argv[1].rstrip("/")


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
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        content = error.read().decode("utf-8")
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            payload = {"raw": content}
        return error.code, payload


health_status, health = request("/health")
if health_status != 200 or health.get("status") != "ok":
    raise SystemExit(f"health failed: {health_status} {health}")

ready_status, ready = request("/ready")
if ready_status != 200 or ready.get("status") != "ok":
    raise SystemExit(f"ready failed: {ready_status} {ready}")

denial_status, denial = request(
    "/v1/quiz-items/next",
    method="POST",
    payload={
        "consumer_id": "consumer_no_entitlement",
        "cefr_level": "A2",
        "theme_ids": ["T10"],
    },
    headers={"X-Consumer-Id": "consumer_no_entitlement"},
)
if denial_status != 403 or denial.get("reason_code") != "ENTITLEMENT_MISSING_FEATURE":
    raise SystemExit(f"entitlement denial failed: {denial_status} {denial}")

print("smoke-ok")
PY
