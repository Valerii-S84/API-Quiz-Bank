#!/usr/bin/env python3
"""Run protected health/ready and business-route load smoke evidence."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_PATH = ROOT / "reports" / "scale" / "protected_business_route_load_smoke_2026-06-11.json"
MODE_HEALTH_READY = "health_ready_only"
MODE_BUSINESS = "business_route_with_test_tenant"
BUSINESS_PATH = "/v1/quiz-items/next"
@dataclass(frozen=True)
class LoadProfile:
    name: str
    concurrency: int
    total_requests: int
    batch_size: int
    timeout_seconds: float
    p95_threshold_ms: float
@dataclass(frozen=True)
class SmokeConfig:
    mode: str
    base_url: str
    edge_api_key: str
    report_path: Path
    server_git_commit_sha: str
    business_consumer_id: str | None
    business_consumer_api_key: str | None
    business_tenant_isolated: bool
    business_expected_status: int
    business_cefr_level: str
    business_theme_id: str
    business_quota_limit: int | None
    health_ready_profile: LoadProfile
    business_profile: LoadProfile
    instability_ratio: float
@dataclass(frozen=True)
class RequestSpec:
    label: str
    method: str
    path: str
    headers: dict[str, str]
    payload: dict[str, object] | None
    expected_statuses: tuple[int, ...]
def main() -> int:
    args = parse_args()
    config, issues = read_config(args)
    if config is None:
        report = build_preflight_report(args, issues)
        emit_report(config_path(args), report)
        return 1
    controls = run_controls(config)
    if controls_failed(controls):
        report = build_report(config, controls, [], "stopped_auth_gate_unexpected")
        emit_report(config.report_path, report)
        return 1
    profile_results, stop_reason = run_profiles(config)
    report = build_report(config, controls, profile_results, stop_reason)
    emit_report(config.report_path, report)
    return 0 if report["conclusion"] == "GO protected business-route load evidence for tested threshold" else 1
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run protected business-route load smoke evidence")
    parser.add_argument("--mode", choices=[MODE_HEALTH_READY, MODE_BUSINESS], default=None)
    parser.add_argument("--output", default=None, help="Report path. Use '-' for sanitized JSON stdout.")
    return parser.parse_args()
def read_config(args: argparse.Namespace) -> tuple[SmokeConfig | None, list[str]]:
    missing: list[str] = []
    errors: list[str] = []
    mode = args.mode or os.getenv("API_QUIZ_BANK_LOAD_SMOKE_MODE", MODE_BUSINESS).strip()
    base_url = required_env("API_QUIZ_BANK_BASE_URL", missing)
    edge_key = secret_from_env_or_file(
        "API_QUIZ_BANK_PUBLIC_API_KEY",
        "API_QUIZ_BANK_PUBLIC_API_KEY_FILE",
        missing,
        errors,
    )
    server_sha = os.getenv("API_QUIZ_BANK_SERVER_GIT_SHA", "").strip() or "unknown"
    consumer_id = os.getenv("API_QUIZ_BANK_LOAD_SMOKE_TEST_CONSUMER_ID", "").strip() or None
    consumer_key = secret_from_env_or_file(
        "API_QUIZ_BANK_LOAD_SMOKE_TEST_CONSUMER_API_KEY",
        "API_QUIZ_BANK_LOAD_SMOKE_TEST_CONSUMER_API_KEY_FILE",
        missing if mode == MODE_BUSINESS else [],
        errors,
        required=mode == MODE_BUSINESS,
    )
    isolated = bool_env("API_QUIZ_BANK_LOAD_SMOKE_TEST_TENANT_ISOLATED", False)
    if mode == MODE_BUSINESS and not consumer_id:
        missing.append("API_QUIZ_BANK_LOAD_SMOKE_TEST_CONSUMER_ID")
    if mode == MODE_BUSINESS and not isolated:
        errors.append("business route requires isolated test tenant/key confirmation")
    if mode not in {MODE_HEALTH_READY, MODE_BUSINESS}:
        errors.append(f"invalid mode: {mode}")
    if missing or errors:
        return None, [f"missing:{item}" for item in missing] + errors
    try:
        return build_config(args, mode, base_url, edge_key, server_sha, consumer_id, consumer_key, isolated), []
    except ValueError as exc:
        return None, [str(exc)]
def build_config(
    args: argparse.Namespace,
    mode: str,
    base_url: str,
    edge_key: str,
    server_sha: str,
    consumer_id: str | None,
    consumer_key: str | None,
    isolated: bool,
) -> SmokeConfig:
    errors: list[str] = []
    health_total = int_env("API_QUIZ_BANK_HEALTH_READY_TOTAL_REQUESTS", 100, errors, 1)
    health_concurrency = int_env("API_QUIZ_BANK_HEALTH_READY_CONCURRENCY", 5, errors, 1)
    business_total = int_env("API_QUIZ_BANK_BUSINESS_ROUTE_TOTAL_REQUESTS", 60, errors, 1)
    business_concurrency = int_env("API_QUIZ_BANK_BUSINESS_ROUTE_CONCURRENCY", 3, errors, 1)
    business_quota_limit = optional_int_env("API_QUIZ_BANK_LOAD_SMOKE_TEST_QUOTA_LIMIT", errors)
    if errors:
        raise ValueError("; ".join(errors))
    return SmokeConfig(
        mode=mode,
        base_url=base_url.rstrip("/"),
        edge_api_key=edge_key,
        report_path=config_path(args),
        server_git_commit_sha=server_sha,
        business_consumer_id=consumer_id,
        business_consumer_api_key=consumer_key,
        business_tenant_isolated=isolated,
        business_expected_status=int(os.getenv("API_QUIZ_BANK_BUSINESS_ROUTE_EXPECTED_STATUS", "200")),
        business_cefr_level=os.getenv("API_QUIZ_BANK_BUSINESS_ROUTE_CEFR_LEVEL", "A2").strip(),
        business_theme_id=os.getenv("API_QUIZ_BANK_BUSINESS_ROUTE_THEME_ID", "T10").strip(),
        business_quota_limit=business_quota_limit,
        health_ready_profile=LoadProfile("health_ready", health_concurrency, health_total, 20, 5.0, 1000.0),
        business_profile=LoadProfile("business_route", business_concurrency, business_total, 20, 8.0, 1500.0),
        instability_ratio=float(os.getenv("API_QUIZ_BANK_LOAD_SMOKE_LATENCY_INSTABILITY_RATIO", "1.8")),
    )
def run_controls(config: SmokeConfig) -> dict[str, dict[str, object]]:
    specs = [
        RequestSpec("health_no_key", "GET", "/health", {}, None, (401,)),
        RequestSpec("health_wrong_key", "GET", "/health", {"X-API-Key": "invalid-load-smoke-key"}, None, (401,)),
        RequestSpec("health_with_edge_key", "GET", "/health", edge_headers(config), None, (200,)),
        RequestSpec("ready_with_edge_key", "GET", "/ready", edge_headers(config), None, (200,)),
    ]
    if config.mode == MODE_BUSINESS:
        specs.extend(business_control_specs(config))
    return {spec.label: control_result(execute_request(config.base_url, spec, 8.0), spec) for spec in specs}
def business_control_specs(config: SmokeConfig) -> list[RequestSpec]:
    payload = business_payload(config)
    mismatch_payload = dict(payload)
    mismatch_payload["consumer_id"] = "load_smoke_mismatch_control"
    return [
        RequestSpec("business_missing_consumer_key", "POST", BUSINESS_PATH, edge_headers(config), payload, (401,)),
        RequestSpec("business_wrong_consumer_key", "POST", BUSINESS_PATH, business_headers(config, "invalid-load-smoke-key"), payload, (401,)),
        RequestSpec("business_mismatched_consumer", "POST", BUSINESS_PATH, business_headers(config, config.business_consumer_api_key or ""), mismatch_payload, (403,)),
        RequestSpec("business_test_key_control", "POST", BUSINESS_PATH, business_headers(config, config.business_consumer_api_key or ""), payload, (config.business_expected_status,)),
    ]
def run_profiles(config: SmokeConfig) -> tuple[list[dict[str, object]], str]:
    results: list[dict[str, object]] = []
    health_result = run_profile(config, config.health_ready_profile, health_ready_specs(config))
    results.append(health_result)
    if health_result["stop_condition_status"] != "completed":
        return results, str(health_result["stop_condition_status"])
    if config.mode != MODE_BUSINESS:
        return results, "completed"
    business_result = run_profile(config, config.business_profile, [business_load_spec(config)])
    results.append(business_result)
    return results, str(business_result["stop_condition_status"])
def run_profile(config: SmokeConfig, profile: LoadProfile, specs: list[RequestSpec]) -> dict[str, object]:
    results: list[dict[str, object]] = []
    previous_p95 = 0.0
    stop_reason = "completed"
    while len(results) < profile.total_requests:
        remaining = profile.total_requests - len(results)
        results.extend(run_batch(config.base_url, profile, specs, min(profile.batch_size, remaining)))
        summary = summarize_results(results)
        p95 = float(summary["p95_ms"])
        if summary["five_xx_count"] > 0:
            stop_reason = "stopped_5xx_detected"
            break
        if summary["timeout_count"] > 0:
            stop_reason = "stopped_timeout"
            break
        if summary["error_count"] > 0:
            stop_reason = "stopped_unexpected_status"
            break
        if p95 > profile.p95_threshold_ms:
            stop_reason = "stopped_p95_threshold_exceeded"
            break
        if previous_p95 and p95 > previous_p95 * config.instability_ratio:
            stop_reason = "stopped_latency_instability"
            break
        previous_p95 = p95
    summary = summarize_results(results)
    return {
        "name": profile.name,
        "concurrency": profile.concurrency,
        "total_requests": profile.total_requests,
        "total_requests_executed": len(results),
        "timeout_seconds": profile.timeout_seconds,
        "p95_threshold_ms": profile.p95_threshold_ms,
        "stop_condition_status": stop_reason,
        **summary,
    }
def run_batch(base_url: str, profile: LoadProfile, specs: list[RequestSpec], count: int) -> list[dict[str, object]]:
    batch = [specs[index % len(specs)] for index in range(count)]
    with ThreadPoolExecutor(max_workers=profile.concurrency) as executor:
        futures = [executor.submit(execute_request, base_url, spec, profile.timeout_seconds) for spec in batch]
        return [future.result() for future in as_completed(futures)]
def execute_request(base_url: str, spec: RequestSpec, timeout_seconds: float) -> dict[str, object]:
    start = datetime.now(UTC).timestamp()
    headers = dict(spec.headers)
    body = None
    if spec.payload is not None:
        body = json.dumps(spec.payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(f"{base_url}{spec.path}", data=body, headers=headers, method=spec.method)
    status, timeout, network_error = perform_request(request, timeout_seconds)
    latency_ms = (datetime.now(UTC).timestamp() - start) * 1000.0
    return {
        "label": spec.label,
        "path": spec.path,
        "status": status,
        "expected_statuses": list(spec.expected_statuses),
        "timeout": timeout,
        "network_error": network_error,
        "latency_ms": latency_ms,
    }
def perform_request(request: Request, timeout_seconds: float) -> tuple[int | None, bool, bool]:
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            response.read()
            return response.status, False, False
    except HTTPError as error:
        return error.code, False, False
    except (TimeoutError, socket.timeout):
        return None, True, True
    except URLError as error:
        return None, isinstance(error.reason, socket.timeout), True
def summarize_results(results: list[dict[str, object]]) -> dict[str, object]:
    status_counts: dict[str, int] = {}
    path_status_counts: dict[str, dict[str, int]] = {}
    error_count = 0
    five_xx_count = 0
    timeout_count = 0
    for result in results:
        status_key = status_count_key(result)
        status_counts[status_key] = status_counts.get(status_key, 0) + 1
        path = str(result["path"])
        path_status_counts.setdefault(path, {})
        path_status_counts[path][status_key] = path_status_counts[path].get(status_key, 0) + 1
        if result["timeout"]:
            timeout_count += 1
        if is_5xx(result["status"]):
            five_xx_count += 1
        if result_is_error(result):
            error_count += 1
    p50, p95, p99 = latency_percentiles(results)
    return {
        "p50_ms": round(p50, 3),
        "p95_ms": round(p95, 3),
        "p99_ms": round(p99, 3),
        "status_counts": status_counts,
        "path_status_counts": path_status_counts,
        "five_xx_count": five_xx_count,
        "timeout_count": timeout_count,
        "error_count": error_count,
    }
def build_report(
    config: SmokeConfig,
    controls: dict[str, dict[str, object]],
    profile_results: list[dict[str, object]],
    stop_reason: str,
) -> dict[str, object]:
    business_result = named_profile(profile_results, "business_route")
    selected_summary = business_result or named_profile(profile_results, "health_ready") or empty_summary()
    business_tested = bool(business_result and business_result["total_requests_executed"])
    business_passed = business_tested and business_result["stop_condition_status"] == "completed"
    return {
        "report_type": "protected_business_route_load_smoke",
        "generated_at": now_utc_iso(),
        "local_git_commit_sha": local_git_commit_sha(),
        "server_git_commit_sha": config.server_git_commit_sha,
        "target_host": target_host(config.base_url),
        "endpoint_list": endpoint_list(config),
        "route_profile": config.mode,
        "business_route_tested": business_tested,
        "business_route_path": BUSINESS_PATH,
        "test_consumer_id": config.business_consumer_id,
        "test_key_hash_prefix": key_hash_prefix(config.business_consumer_api_key),
        "test_key_fingerprint": key_fingerprint(config.business_consumer_api_key),
        "test_tenant_key_isolation": bool(config.business_tenant_isolated and config.business_consumer_id),
        "test_tenant_ref": config.business_consumer_id if config.business_tenant_isolated else None,
        "state_changing_route_used": business_tested,
        "quota_counter_pollution_risk": pollution_risk(config.mode, business_tested),
        "concurrency": selected_summary["concurrency"],
        "total_requests": selected_summary["total_requests"],
        "total_requests_executed": selected_summary["total_requests_executed"],
        "p50_ms": selected_summary["p50_ms"],
        "p95_ms": selected_summary["p95_ms"],
        "p99_ms": selected_summary["p99_ms"],
        "status_counts": selected_summary["status_counts"],
        "five_xx_count": selected_summary["five_xx_count"],
        "timeout_count": selected_summary["timeout_count"],
        "error_count": selected_summary["error_count"],
        "auth_gate_result": auth_gate_result(controls),
        "health_result": health_result(controls, profile_results),
        "ready_result": ready_result(controls, profile_results),
        "business_route_result": business_route_result(controls, business_result),
        "negative_controls": negative_controls(controls, config.mode),
        "quota_entitlement_control_result": quota_entitlement_control(config, controls, business_result),
        "load_profiles": profile_results,
        "stop_condition_status": stop_reason,
        "conclusion": conclusion(config.mode, business_passed, stop_reason),
        "explicit_non_claims": explicit_non_claims(),
    }
def build_preflight_report(args: argparse.Namespace, issues: list[str]) -> dict[str, object]:
    mode = args.mode or os.getenv("API_QUIZ_BANK_LOAD_SMOKE_MODE", MODE_BUSINESS).strip()
    config = default_config(args, mode)
    stop_reason = "stopped_missing_required_env" if has_missing_issue(issues) else "stopped_invalid_config"
    report = build_report(config, {}, [], stop_reason)
    report["stop_condition_reasons"] = issues
    if mode == MODE_BUSINESS and has_missing_test_tenant_issue(issues):
        report["conclusion"] = "PARTIAL isolated test consumer/key missing; business-route load not executed"
    return report
def control_result(response: dict[str, object], spec: RequestSpec) -> dict[str, object]:
    return {
        "expected_statuses": list(spec.expected_statuses),
        "actual_status": response["status"],
        "timeout": response["timeout"],
        "ok": response["status"] in spec.expected_statuses and not response["timeout"],
    }
def controls_failed(controls: dict[str, dict[str, object]]) -> bool:
    return any(not result["ok"] for result in controls.values())
def health_ready_specs(config: SmokeConfig) -> list[RequestSpec]:
    return [
        RequestSpec("health_load", "GET", "/health", edge_headers(config), None, (200,)),
        RequestSpec("ready_load", "GET", "/ready", edge_headers(config), None, (200,)),
    ]
def business_load_spec(config: SmokeConfig) -> RequestSpec:
    return RequestSpec(
        "business_route_load", "POST", BUSINESS_PATH,
        business_headers(config, config.business_consumer_api_key or ""), business_payload(config),
        (config.business_expected_status,),
    )
def business_payload(config: SmokeConfig) -> dict[str, object]:
    return {"consumer_id": config.business_consumer_id or "", "cefr_level": config.business_cefr_level, "theme_ids": [config.business_theme_id]}
def business_headers(config: SmokeConfig, consumer_key: str) -> dict[str, str]:
    return {"X-API-Key": config.edge_api_key, "X-Consumer-Id": config.business_consumer_id or "", "X-QuizBank-API-Key": consumer_key}
def edge_headers(config: SmokeConfig) -> dict[str, str]:
    return {"X-API-Key": config.edge_api_key}
def endpoint_list(config: SmokeConfig) -> list[dict[str, object]]:
    endpoints = [
        {"label": "health_no_key", "method": "GET", "path": "/health", "expected_status": 401},
        {"label": "health_with_edge_key", "method": "GET", "path": "/health", "expected_status": 200},
        {"label": "ready_with_edge_key", "method": "GET", "path": "/ready", "expected_status": 200},
        {
            "label": "business_route", "method": "POST", "path": BUSINESS_PATH,
            "expected_status": config.business_expected_status, "included_in_mode": config.mode == MODE_BUSINESS,
        },
    ]
    return endpoints
def auth_gate_result(controls: dict[str, dict[str, object]]) -> dict[str, object]:
    keys = ("health_no_key", "health_wrong_key", "health_with_edge_key", "ready_with_edge_key")
    return {key: controls.get(key, not_run()) for key in keys}
def health_result(controls: dict[str, dict[str, object]], profiles: list[dict[str, object]]) -> dict[str, object]:
    profile = named_profile(profiles, "health_ready")
    return {
        "no_key": controls.get("health_no_key", not_run()), "wrong_key": controls.get("health_wrong_key", not_run()),
        "authorized": controls.get("health_with_edge_key", not_run()), "load": path_summary(profile, "/health"),
    }
def ready_result(controls: dict[str, dict[str, object]], profiles: list[dict[str, object]]) -> dict[str, object]:
    profile = named_profile(profiles, "health_ready")
    return {"authorized": controls.get("ready_with_edge_key", not_run()), "load": path_summary(profile, "/ready")}
def business_route_result(
    controls: dict[str, dict[str, object]],
    profile: dict[str, object] | None,
) -> dict[str, object]:
    return {
        "path": BUSINESS_PATH, "tested": bool(profile and profile["total_requests_executed"]),
        "passed_threshold": bool(profile and profile["stop_condition_status"] == "completed"), "load": profile or not_run(),
        "test_key_control": controls.get("business_test_key_control", not_run()),
        "missing_consumer_key": controls.get("business_missing_consumer_key", not_run()),
        "wrong_consumer_key": controls.get("business_wrong_consumer_key", not_run()),
        "mismatched_consumer": controls.get("business_mismatched_consumer", not_run()),
    }
def quota_entitlement_control(
    config: SmokeConfig,
    controls: dict[str, dict[str, object]],
    profile: dict[str, object] | None,
) -> dict[str, object]:
    return {
        "test_consumer_id": config.business_consumer_id, "expected_feature": "quiz_delivery",
        "expected_daily_quota_limit": config.business_quota_limit,
        "test_tenant_key_isolation": bool(config.business_tenant_isolated and config.business_consumer_id),
        "positive_business_control": controls.get("business_test_key_control", not_run()),
        "business_load_completed": bool(profile and profile["stop_condition_status"] == "completed"),
        "quota_counter_pollution_risk": pollution_risk(config.mode, bool(profile)),
        "validation_basis": "isolated test consumer/key plus successful protected business route responses",
    }
def negative_controls(controls: dict[str, dict[str, object]], mode: str) -> dict[str, object]:
    result = {
        "no_key_health": controls.get("health_no_key", not_run()), "wrong_edge_key_health": controls.get("health_wrong_key", not_run()),
    }
    if mode == MODE_BUSINESS:
        result.update(
            {
                "missing_consumer_key": controls.get("business_missing_consumer_key", not_run()),
                "wrong_consumer_key": controls.get("business_wrong_consumer_key", not_run()), "mismatched_consumer": controls.get("business_mismatched_consumer", not_run()),
            }
        )
    return result
def conclusion(mode: str, business_tested: bool, stop_reason: str) -> str:
    if stop_reason == "stopped_auth_gate_unexpected":
        return "PARTIAL protected business-route load smoke stopped: stopped_auth_gate_unexpected"
    if mode == MODE_BUSINESS and business_tested and stop_reason == "completed":
        return "GO protected business-route load evidence for tested threshold"
    if mode == MODE_HEALTH_READY and stop_reason == "completed":
        return "PARTIAL protected edge/health/ready only; business-route load remains open"
    if mode == MODE_BUSINESS and not business_tested:
        return "PARTIAL isolated test consumer/key missing; business-route load not executed"
    return f"PARTIAL protected business-route load smoke stopped: {stop_reason}"
def pollution_risk(mode: str, business_tested: bool) -> str:
    if business_tested:
        return "isolated"
    if mode == MODE_HEALTH_READY:
        return "none"
    return "unknown"
def has_missing_issue(issues: list[str]) -> bool:
    return any(issue.startswith("missing:") for issue in issues)
def has_missing_test_tenant_issue(issues: list[str]) -> bool:
    return any("TEST_CONSUMER" in issue or "isolated test tenant" in issue for issue in issues)
def explicit_non_claims() -> dict[str, bool]:
    return {
        "not_paid_launch_approval": True, "not_legal_privacy_approval": True,
        "not_support_sla_approval": True, "not_school_launch_approval": True,
        "not_unlimited_broad_scale_proof": True,
    }
def path_summary(profile: dict[str, object] | None, path: str) -> dict[str, object]:
    if profile is None:
        return not_run()
    counts = profile.get("path_status_counts", {})
    return {"status_counts": counts.get(path, {}), "profile": profile["name"]}
def named_profile(profiles: list[dict[str, object]], name: str) -> dict[str, object] | None:
    for profile in profiles:
        if profile["name"] == name:
            return profile
    return None
def empty_summary() -> dict[str, object]:
    return {
        "concurrency": 0, "total_requests": 0, "total_requests_executed": 0,
        "p50_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0, "status_counts": {},
        "five_xx_count": 0, "timeout_count": 0, "error_count": 0,
    }
def not_run() -> dict[str, object]:
    return {"status": "not_run", "ok": False}
def status_count_key(result: dict[str, object]) -> str:
    if result["timeout"]:
        return "timeout"
    if result["status"] is None:
        return "network_error"
    return str(int(result["status"]))
def result_is_error(result: dict[str, object]) -> bool:
    return bool(result["timeout"]) or result["status"] not in result["expected_statuses"]
def is_5xx(status: object) -> bool:
    return isinstance(status, int) and 500 <= status < 600
def latency_percentiles(results: list[dict[str, object]]) -> tuple[float, float, float]:
    if not results:
        return 0.0, 0.0, 0.0
    values = sorted(float(result["latency_ms"]) for result in results)
    return percentile(values, 50), percentile(values, 95), percentile(values, 99)
def percentile(values: list[float], level: int) -> float:
    return float(values[int((len(values) - 1) * level / 100)])
def required_env(name: str, missing: list[str]) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        missing.append(name)
    return value
def secret_from_env_or_file(
    env_name: str,
    file_env_name: str,
    missing: list[str],
    errors: list[str],
    required: bool = True,
) -> str | None:
    value = os.getenv(env_name, "").strip()
    if value:
        return value
    key_file = os.getenv(file_env_name, "").strip()
    if key_file:
        return read_secret_file(key_file, env_name, errors)
    if required:
        missing.append(env_name)
        missing.append(file_env_name)
    return None
def read_secret_file(key_file: str, env_name: str, errors: list[str]) -> str | None:
    try:
        value = Path(key_file).read_text(encoding="utf-8").strip()
    except OSError as exc:
        errors.append(f"cannot read file for {env_name}: {exc.__class__.__name__}")
        return None
    if not value:
        errors.append(f"file for {env_name} is empty")
        return None
    return value
def int_env(name: str, default: int, errors: list[str], minimum: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        errors.append(f"invalid int for {name}")
        return default
    if value < minimum:
        errors.append(f"value below minimum for {name}")
        return minimum
    return value
def optional_int_env(name: str, errors: list[str]) -> int | None:
    raw = os.getenv(name, "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        errors.append(f"invalid int for {name}")
        return None
def key_hash_prefix(raw_key: str | None) -> str | None:
    return None if raw_key is None else hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]
def key_fingerprint(raw_key: str | None) -> str | None:
    return None if raw_key is None else hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:24]
def bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name, "").strip().lower()
    return default if not raw else raw in {"1", "true", "yes", "on", "y"}
def default_config(args: argparse.Namespace, mode: str) -> SmokeConfig:
    return SmokeConfig(
        mode=mode,
        base_url=os.getenv("API_QUIZ_BANK_BASE_URL", "unknown").strip() or "unknown",
        edge_api_key="",
        report_path=config_path(args),
        server_git_commit_sha=os.getenv("API_QUIZ_BANK_SERVER_GIT_SHA", "").strip() or "unknown",
        business_consumer_id=os.getenv("API_QUIZ_BANK_LOAD_SMOKE_TEST_CONSUMER_ID", "").strip() or None,
        business_consumer_api_key=None,
        business_tenant_isolated=bool_env("API_QUIZ_BANK_LOAD_SMOKE_TEST_TENANT_ISOLATED", False),
        business_expected_status=200,
        business_cefr_level="A2",
        business_theme_id="T10",
        business_quota_limit=None,
        health_ready_profile=LoadProfile("health_ready", 5, 100, 20, 5.0, 1000.0),
        business_profile=LoadProfile("business_route", 3, 60, 20, 8.0, 1500.0),
        instability_ratio=1.8,
    )
def config_path(args: argparse.Namespace | None) -> Path:
    if args is not None and args.output:
        return Path(args.output)
    report_path = os.getenv("API_QUIZ_BANK_LOAD_SMOKE_REPORT_PATH", "").strip()
    return Path(report_path) if report_path else DEFAULT_REPORT_PATH
def emit_report(path: Path, report: dict[str, object]) -> None:
    if str(path) == "-":
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(path), "stop_condition": report["stop_condition_status"]}))
def target_host(base_url: str) -> str:
    return base_url.replace("https://", "").replace("http://", "").rstrip("/") or "unknown"
def now_utc_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
def local_git_commit_sha() -> str:
    env_sha = os.getenv("API_QUIZ_BANK_LOCAL_GIT_SHA", "").strip()
    if env_sha:
        return env_sha
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"
if __name__ == "__main__":
    raise SystemExit(main())
