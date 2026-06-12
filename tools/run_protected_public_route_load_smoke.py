#!/usr/bin/env python3
"""Run a limited protected public-route load smoke for the owner-operated runtime."""
from __future__ import annotations
import argparse
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
DEFAULT_REPORT_PATH = ROOT / "reports" / "scale" / "protected_public_route_load_smoke_2026-06-11.json"
DEFAULT_CONCURRENCY = 5
DEFAULT_TOTAL_REQUESTS = 100
DEFAULT_BATCH_SIZE = 20
DEFAULT_TIMEOUT_SECONDS = 5.0
DEFAULT_P95_THRESHOLD_MS = 1000.0
DEFAULT_MAX_ERROR_RATE = 0.0
DEFAULT_INSTABILITY_RATIO = 1.8
@dataclass(frozen=True)
class SmokeConfig:
    base_url: str
    edge_api_key: str
    report_path: Path
    concurrency: int
    total_requests: int
    batch_size: int
    timeout_seconds: float
    p95_threshold_ms: float
    max_error_rate: float
    instability_ratio: float
    use_state_route: bool
    route_profile: str
    server_git_commit_sha: str
    state_consumer_id: str | None = None
    state_consumer_api_key: str | None = None
def main() -> int:
    args = parse_args()
    config, validation_issues = read_config(args)
    report_path = config_path(args)
    if config is None:
        report = build_preflight_report(validation_issues, report_path)
        if str(report_path) == "-":
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            write_report(report_path, report)
            print(json.dumps({"report": str(report_path), "stop_condition": report["stop_condition_status"]}))
        return 1
    auth_gate = run_auth_gate(config)
    if not all(entry["ok"] for entry in auth_gate.values()):
        report = build_report(config, auth_gate, [], "stopped_auth_gate_unexpected", 0.0, 0.0, 0.0)
        if str(config.report_path) == "-":
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            write_report(config.report_path, report)
            print(json.dumps({"report": str(config.report_path), "stop_condition": "stopped_auth_gate_unexpected"}))
        return 1
    report_payload = run_load_smoke(config, auth_gate)
    if str(config.report_path) == "-":
        print(json.dumps(report_payload["report"], indent=2, sort_keys=True))
    else:
        write_report(config.report_path, report_payload["report"])
        print(json.dumps({"report": str(config.report_path), "stop_condition": report_payload["stop_condition"]}))
    return report_payload["exit_code"]
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a limited protected public-route load smoke")
    parser.add_argument(
        "--output",
        default=None,
        help="Report path. Use '-' to print report JSON to stdout.",
    )
    return parser.parse_args()
def resolve_repo_root() -> Path:
    explicit_root = os.getenv("API_QUIZ_BANK_TOOL_PROJECT_ROOT", "").strip()
    candidates = [ROOT]
    if explicit_root:
        candidates.insert(0, Path(explicit_root))
    candidates.insert(0, Path.cwd())
    checked: set[Path] = set()
    for candidate in candidates:
        path = candidate
        steps = 0
        while path not in checked and steps < 6:
            checked.add(path)
            if (path / ".git").exists():
                return path
            parent = path.parent
            if parent == path:
                break
            path = parent
            steps += 1
    return candidates[0]
def read_config(args: argparse.Namespace) -> tuple[SmokeConfig | None, list[str]]:
    missing: list[str] = []
    errors: list[str] = []
    base_url = read_required_env("API_QUIZ_BANK_BASE_URL", missing)
    edge_api_key = read_api_key(missing, errors)
    server_git_commit_sha = os.getenv("API_QUIZ_BANK_SERVER_GIT_SHA", "").strip() or "unknown"
    total_requests = read_int_env("API_QUIZ_BANK_LOAD_SMOKE_TOTAL_REQUESTS", DEFAULT_TOTAL_REQUESTS, errors, minimum=1)
    concurrency = read_int_env("API_QUIZ_BANK_LOAD_SMOKE_CONCURRENCY", DEFAULT_CONCURRENCY, errors, minimum=1)
    batch_size = read_int_env(
        "API_QUIZ_BANK_LOAD_SMOKE_BATCH_SIZE", DEFAULT_BATCH_SIZE, errors, minimum=1, maximum=max(total_requests, 1)
    )
    timeout_seconds = read_float_env(
        "API_QUIZ_BANK_LOAD_SMOKE_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS, errors, minimum=0.1
    )
    p95_threshold_ms = read_float_env(
        "API_QUIZ_BANK_LOAD_SMOKE_P95_THRESHOLD_MS", DEFAULT_P95_THRESHOLD_MS, errors, minimum=1.0
    )
    max_error_rate = read_float_env(
        "API_QUIZ_BANK_LOAD_SMOKE_MAX_ERROR_RATE", DEFAULT_MAX_ERROR_RATE, errors, minimum=0.0, maximum=1.0
    )
    instability_ratio = read_float_env(
        "API_QUIZ_BANK_LOAD_SMOKE_LATENCY_INSTABILITY_RATIO", DEFAULT_INSTABILITY_RATIO, errors, minimum=1.0
    )
    use_state_route = read_bool_env("API_QUIZ_BANK_LOAD_SMOKE_USE_STATE_ROUTE", False)
    state_isolated = read_bool_env("API_QUIZ_BANK_LOAD_SMOKE_STATE_ROUTE_ISOLATED", False)
    state_consumer_id = os.getenv("API_QUIZ_BANK_LOAD_SMOKE_STATE_CONSUMER_ID")
    state_consumer_api_key = os.getenv("API_QUIZ_BANK_LOAD_SMOKE_STATE_CONSUMER_API_KEY")
    if use_state_route and not state_isolated:
        errors.append("state route requested without isolation confirmation")
    if use_state_route and (not state_consumer_id or not state_consumer_api_key):
        errors.append("state route requested without test consumer credentials")
    if missing or errors:
        return None, [f"missing:{name}" for name in missing] + errors
    if batch_size > total_requests:
        batch_size = total_requests
    if concurrency > total_requests:
        concurrency = total_requests
    route_profile = "business_route_with_test_tenant" if use_state_route else "health_ready_only"
    return (
        SmokeConfig(
            base_url=base_url.rstrip("/"),
            edge_api_key=edge_api_key,
            report_path=config_path(args),
            concurrency=concurrency,
            total_requests=total_requests,
            batch_size=batch_size,
            timeout_seconds=timeout_seconds,
            p95_threshold_ms=p95_threshold_ms,
            max_error_rate=max_error_rate,
            instability_ratio=instability_ratio,
            use_state_route=use_state_route,
            route_profile=route_profile,
            server_git_commit_sha=server_git_commit_sha,
            state_consumer_id=state_consumer_id,
            state_consumer_api_key=state_consumer_api_key,
        ),
        [],
    )
def run_load_smoke(config: SmokeConfig, auth_gate: dict[str, dict[str, object]]) -> dict[str, object]:
    load_specs = build_load_specs(config)
    batch_results: list[dict[str, object]] = []
    previous_p95 = None
    stop_reason = "completed"
    for _ in range(10000):
        if len(batch_results) >= config.total_requests:
            break
        remaining = config.total_requests - len(batch_results)
        batch = run_load_batch(config, load_specs, min(config.batch_size, remaining))
        batch_results.extend(batch)
        p50_ms, p95_ms, p99_ms = latency_percentiles(batch_results)
        status_counts, five_xx_count, timeout_count = summarize_results(batch_results)
        if any(_is_5xx(item["status"]) for item in batch_results):
            stop_reason = "stopped_5xx_detected"
            break
        if timeout_count > 0:
            stop_reason = "stopped_timeout"
            break
        if previous_p95 is not None and p95_ms > previous_p95 * config.instability_ratio:
            stop_reason = "stopped_latency_instability"
            break
        if p95_ms > config.p95_threshold_ms:
            stop_reason = "stopped_p95_threshold_exceeded"
            break
        if error_rate(batch_results) > config.max_error_rate:
            stop_reason = "stopped_error_rate_exceeded"
            break
        previous_p95 = p95_ms
    p50_ms, p95_ms, p99_ms = latency_percentiles(batch_results)
    return {
        "exit_code": 0 if stop_reason == "completed" else 1,
        "stop_condition": stop_reason,
        "print_payload": {"report": str(config.report_path), "stop_condition": stop_reason},
        "report": build_report(
            config=config,
            auth_gate=auth_gate,
            load_results=batch_results,
            stop_reason=stop_reason,
            p50_ms=p50_ms,
            p95_ms=p95_ms,
            p99_ms=p99_ms,
        ),
    }
def build_preflight_report(issues: list[str], report_path: Path) -> dict[str, object]:
    stopped = "stopped_invalid_config"
    if any(item.startswith("missing:") for item in issues):
        stopped = "stopped_missing_required_env"
    return {
        "report_type": "protected_public_route_load_smoke",
        "generated_at": now_utc_iso(),
        "git_commit_sha": git_commit_sha(),
        "server_git_commit_sha": "unknown",
        "target_host": "unknown",
        "endpoint_list": endpoint_list(default_smoke_config()),
        "route_profile": "health_ready_only",
        "concurrency": DEFAULT_CONCURRENCY,
        "batch_size": DEFAULT_BATCH_SIZE,
        "total_requests": DEFAULT_TOTAL_REQUESTS,
        "total_requests_executed": 0,
        "p50_ms": 0.0,
        "p95_ms": 0.0,
        "p99_ms": 0.0,
        "status_counts": {},
        "five_xx_count": 0,
        "timeout_count": 0,
        "stop_condition_status": stopped,
        "stop_condition_reasons": issues,
        "auth_gate": {
            "health_no_key": {"expected_status": 401, "actual_status": None, "timeout": False, "ok": False},
            "health_with_edge_key": {"expected_status": 200, "actual_status": None, "timeout": False, "ok": False},
            "ready_with_edge_key": {"expected_status": 200, "actual_status": None, "timeout": False, "ok": False},
        },
        "auth_gate_result": {
            "health_no_key": {"expected_status": 401, "actual_status": None, "timeout": False, "ok": False},
            "health_with_edge_key": {"expected_status": 200, "actual_status": None, "timeout": False, "ok": False},
            "ready_with_edge_key": {"expected_status": 200, "actual_status": None, "timeout": False, "ok": False},
        },
        "ready_health_result": {
            "health_no_key_status": None,
            "health_with_edge_key_status": None,
            "ready_with_edge_key_status": None,
        },
        "health_result": {
            "no_key_status": None,
            "with_edge_key_status": None,
        },
        "ready_result": None,
        "state_changing_route_used": False,
        "state_route_tenant_isolated": False,
        "conclusion": "not run: preflight validation failed",
        "non_claims": {
            "not_broad_scale_readiness": True,
            "not_paid_launch_readiness": True,
            "not_legal_privacy_approval": True,
            "not_support_sla_approval": True,
            "not_school_launch_readiness": True,
        },
        "report_path": str(report_path),
    }
def default_smoke_config() -> SmokeConfig:
    return SmokeConfig(
        base_url="unknown",
        edge_api_key="",
        report_path=config_path(None),
        concurrency=DEFAULT_CONCURRENCY,
        total_requests=DEFAULT_TOTAL_REQUESTS,
        batch_size=DEFAULT_BATCH_SIZE,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
        p95_threshold_ms=DEFAULT_P95_THRESHOLD_MS,
        max_error_rate=DEFAULT_MAX_ERROR_RATE,
        instability_ratio=DEFAULT_INSTABILITY_RATIO,
        use_state_route=False,
        route_profile="health_ready_only",
        server_git_commit_sha="unknown",
    )
def run_auth_gate(config: SmokeConfig) -> dict[str, dict[str, object]]:
    results: dict[str, dict[str, object]] = {}
    for spec in build_auth_gateway_specs(config):
        response = execute_request(config.base_url, spec, config.timeout_seconds)
        results[spec["label"]] = {
            "expected_status": spec["expected_status"],
            "actual_status": response["status"],
            "timeout": response["timeout"],
            "ok": response["status"] == spec["expected_status"] and not response["timeout"],
        }
    return results
def build_report(
    config: SmokeConfig,
    auth_gate: dict[str, dict[str, object]],
    load_results: list[dict[str, object]],
    stop_reason: str,
    p50_ms: float,
    p95_ms: float,
    p99_ms: float,
) -> dict[str, object]:
    status_counts, five_xx_count, timeout_count = summarize_results(load_results)
    return {
        "report_type": "protected_public_route_load_smoke",
        "generated_at": now_utc_iso(),
        "git_commit_sha": git_commit_sha(),
        "server_git_commit_sha": config.server_git_commit_sha,
        "target_host": config.base_url.replace("https://", "").replace("http://", ""),
        "endpoint_list": endpoint_list(config),
        "route_profile": config.route_profile,
        "concurrency": config.concurrency,
        "batch_size": config.batch_size,
        "total_requests": config.total_requests,
        "total_requests_executed": len(load_results),
        "p50_ms": round(p50_ms, 3),
        "p95_ms": round(p95_ms, 3),
        "p99_ms": round(p99_ms, 3),
        "status_counts": status_counts,
        "five_xx_count": five_xx_count,
        "timeout_count": timeout_count,
        "stop_condition_status": stop_reason,
        "auth_gate": auth_gate,
        "auth_gate_result": auth_gate,
        "ready_health_result": {
            "health_no_key_status": auth_gate["health_no_key"]["actual_status"],
            "health_with_edge_key_status": auth_gate["health_with_edge_key"]["actual_status"],
            "ready_with_edge_key_status": auth_gate["ready_with_edge_key"]["actual_status"],
        },
        "health_result": {
            "no_key_status": auth_gate["health_no_key"]["actual_status"],
            "with_edge_key_status": auth_gate["health_with_edge_key"]["actual_status"],
        },
        "ready_result": auth_gate["ready_with_edge_key"]["actual_status"],
        "state_changing_route_used": config.use_state_route,
        "state_route_tenant_isolated": bool(
            config.use_state_route and config.state_consumer_id and config.state_consumer_api_key
        ),
        "conclusion": make_conclusion(stop_reason, config, p95_ms),
        "non_claims": {
            "not_broad_scale_readiness": True,
            "not_paid_launch_readiness": True,
            "not_legal_privacy_approval": True,
            "not_support_sla_approval": True,
            "not_school_launch_readiness": True,
        },
        "report_path": str(config.report_path),
    }
def summarize_results(load_results: list[dict[str, object]]) -> tuple[dict[str, int], int, int]:
    status_counts: dict[str, int] = {}
    five_xx_count = 0
    timeout_count = 0
    for result in load_results:
        status = result["status"]
        if result["timeout"]:
            timeout_count += 1
            status_counts["timeout"] = status_counts.get("timeout", 0) + 1
            continue
        if status is None:
            status_counts["network_error"] = status_counts.get("network_error", 0) + 1
            continue
        status_key = str(int(status))
        status_counts[status_key] = status_counts.get(status_key, 0) + 1
        if 500 <= int(status) < 600:
            five_xx_count += 1
    return status_counts, five_xx_count, timeout_count
def endpoint_list(config: SmokeConfig) -> list[dict[str, object]]:
    endpoints = [
        {"method": "GET", "path": "/health", "expected_status": 401},
        {"method": "GET", "path": "/health", "expected_status": 200, "auth": "edge"},
        {"method": "GET", "path": "/ready", "expected_status": 200, "auth": "edge"},
    ]
    if config.use_state_route:
        endpoints.append(
            {"method": "POST", "path": "/v1/quiz-items/next", "expected_status": 200, "state_route": True}
        )
    return endpoints
def build_auth_gateway_specs(config: SmokeConfig) -> list[dict[str, object]]:
    return [
        _spec("GET", "/health", {}, None, 401, label="health_no_key"),
        _spec("GET", "/health", {"X-API-Key": config.edge_api_key}, None, 200, label="health_with_edge_key"),
        _spec("GET", "/ready", {"X-API-Key": config.edge_api_key}, None, 200, label="ready_with_edge_key"),
    ]
def build_load_specs(config: SmokeConfig) -> list[dict[str, object]]:
    specs = [_spec("GET", "/ready", {"X-API-Key": config.edge_api_key}, None, 200)]
    if config.use_state_route:
        specs.append(
            _spec(
                "POST",
                "/v1/quiz-items/next",
                {
                    "X-API-Key": config.edge_api_key,
                    "X-Consumer-Id": config.state_consumer_id,
                    "X-QuizBank-API-Key": config.state_consumer_api_key,
                },
                {"consumer_id": config.state_consumer_id, "cefr_level": "A2", "theme_ids": ["T10"]},
                200,
            )
        )
    return specs
def _spec(
    method: str,
    path: str,
    headers: dict[str, str | None] | None,
    payload: dict[str, object] | None,
    expected_status: int,
    label: str | None = None,
) -> dict[str, object]:
    request_headers: dict[str, str] = {}
    if headers:
        for key, value in headers.items():
            if isinstance(value, str):
                request_headers[key] = value
    return {
        "label": label or f"{path}_{method.lower()}",
        "method": method,
        "path": path,
        "headers": request_headers,
        "payload": payload,
        "expected_status": expected_status,
    }
def run_load_batch(config: SmokeConfig, specs: list[dict[str, object]], count: int) -> list[dict[str, object]]:
    batch = [specs[index % len(specs)] for index in range(count)]
    with ThreadPoolExecutor(max_workers=config.concurrency) as executor:
        futures = [
            executor.submit(execute_request, config.base_url, spec, config.timeout_seconds) for spec in batch
        ]
        return [future.result() for future in as_completed(futures)]
def execute_request(base_url: str, spec: dict[str, object], timeout_seconds: float) -> dict[str, object]:
    start = datetime.now(UTC).timestamp()
    headers = dict(spec["headers"])
    body = None
    payload = spec["payload"]
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(f"{base_url}{spec['path']}", data=body, headers=headers, method=str(spec["method"]))
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            response.read()
            status = response.status
            timeout = False
            network_error = False
    except HTTPError as error:
        status = error.code
        timeout = False
        network_error = False
    except URLError as error:
        status = None
        timeout = isinstance(error.reason, socket.timeout)
        network_error = True
    latency_ms = (datetime.now(UTC).timestamp() - start) * 1000.0
    return {
        "status": status,
        "expected_status": spec["expected_status"],
        "timeout": timeout,
        "network_error": network_error,
        "latency_ms": latency_ms,
    }
def latency_percentiles(results: list[dict[str, object]]) -> tuple[float, float, float]:
    if not results:
        return 0.0, 0.0, 0.0
    latencies = sorted(float(item["latency_ms"]) for item in results)
    return percentile(latencies, 50), percentile(latencies, 95), percentile(latencies, 99)
def percentile(values: list[float], level: int) -> float:
    index = int((len(values) - 1) * level / 100)
    return float(values[index])
def _is_5xx(status: int | None) -> bool:
    return status is not None and status >= 500
def error_rate(results: list[dict[str, object]]) -> float:
    if not results:
        return 0.0
    failed = 0
    for item in results:
        if item["status"] != item["expected_status"] or item["timeout"]:
            failed += 1
    return failed / len(results)
def make_conclusion(stop_reason: str, config: SmokeConfig, p95_ms: float) -> str:
    if stop_reason == "completed":
        if config.route_profile == "health_ready_only":
            return "GO protected edge/health/ready load smoke"
        return "GO business route scale/load"
    if stop_reason == "stopped_auth_gate_unexpected":
        return "Stopped because protected/public auth gate response is not expected."
    if stop_reason == "stopped_5xx_detected":
        return "Stopped because 5xx response observed."
    if stop_reason == "stopped_timeout":
        return "Stopped because timeout_count > 0."
    if stop_reason == "stopped_p95_threshold_exceeded":
        return f"Stopped because p95 exceeded threshold ({p95_ms:.1f}ms > {config.p95_threshold_ms:.1f}ms)."
    if stop_reason == "stopped_latency_instability":
        return "Stopped because p95 latency trend was unstable between batches."
    if stop_reason == "stopped_error_rate_exceeded":
        return "Stopped because error rate exceeded accepted threshold."
    return f"Stopped by configured stop condition: {stop_reason}"
def read_required_env(name: str, missing: list[str]) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        missing.append(name)
    return value
def read_api_key(missing: list[str], errors: list[str]) -> str:
    value = os.getenv("API_QUIZ_BANK_PUBLIC_API_KEY", "").strip()
    if value:
        return value
    key_file = os.getenv("API_QUIZ_BANK_PUBLIC_API_KEY_FILE", "").strip()
    if key_file:
        try:
            value = Path(key_file).read_text(encoding="utf-8").strip()
        except OSError as exc:
            errors.append(f"cannot read API_QUIZ_BANK_PUBLIC_API_KEY_FILE: {exc.__class__.__name__}")
            missing.append("API_QUIZ_BANK_PUBLIC_API_KEY")
            return ""
        if value:
            return value
        errors.append("API_QUIZ_BANK_PUBLIC_API_KEY_FILE is empty")
    missing.append("API_QUIZ_BANK_PUBLIC_API_KEY")
    if not key_file:
        missing.append("API_QUIZ_BANK_PUBLIC_API_KEY_FILE")
    return ""
def read_bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name, "").strip().lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "on", "y"}
def read_int_env(name: str, default: int, errors: list[str], minimum: int | None = None, maximum: int | None = None) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        errors.append(f"invalid int for {name}: {raw}")
        return default
    if minimum is not None and value < minimum:
        errors.append(f"value below minimum for {name}: {value}")
        return minimum
    if maximum is not None and value > maximum:
        errors.append(f"value above maximum for {name}: {value}")
        return maximum
    return value
def read_float_env(
    name: str,
    default: float,
    errors: list[str],
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = float(raw)
    except ValueError:
        errors.append(f"invalid float for {name}: {raw}")
        return default
    if minimum is not None and value < minimum:
        errors.append(f"value below minimum for {name}: {value}")
        return minimum
    if maximum is not None and value > maximum:
        errors.append(f"value above maximum for {name}: {value}")
        return maximum
    return value
def config_path(args: argparse.Namespace | None) -> Path:
    if args is not None and args.output:
        return Path(args.output)
    report_path = os.getenv("API_QUIZ_BANK_LOAD_SMOKE_REPORT_PATH", "").strip()
    if report_path:
        return Path(report_path)
    return resolve_repo_root() / "reports" / "scale" / "protected_public_route_load_smoke_2026-06-11.json"
def now_utc_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
def write_report(path: str | Path, report: dict[str, object]) -> None:
    if str(path) == "-":
        return
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
def git_commit_sha() -> str:
    env_sha = os.getenv("API_QUIZ_BANK_LOCAL_GIT_SHA", "").strip()
    if env_sha:
        return env_sha
    for candidate in [resolve_repo_root(), Path.cwd()]:
        try:
            return subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=candidate, text=True, stderr=subprocess.DEVNULL
            ).strip()
        except Exception:
            continue
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "unknown"
if __name__ == "__main__":
    raise SystemExit(main())
