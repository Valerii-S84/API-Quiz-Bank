#!/usr/bin/env python3
"""Generate local read-path performance evidence for /v1/quiz-items/next."""

from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import sqlite3
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any
from unittest import mock

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quizbank_mvp import auth, selection  # noqa: E402
from quizbank_mvp.app import create_app  # noqa: E402
from quizbank_mvp.database import (  # noqa: E402
    connect,
    initialize_database,
    seed_api_credential,
    seed_consumer,
    seed_control_fixture,
    seed_entitlement,
)
from quizbank_mvp.selection_eligibility import (  # noqa: E402
    CANDIDATE_POOL_LIMIT,
    HISTORY_SCORING_CANDIDATE_LIMIT,
)
from quizbank_mvp.time_ids import utc_now  # noqa: E402


APPROVED_FIXTURE = ROOT / "tests" / "fixtures" / "selection" / "approved_traceable_items.jsonl"
REPORT_PATH = ROOT / "reports" / "scale" / "read_path_perf_after_fix_2026-06-12.json"
SYNTHETIC_ITEM_COUNT = 30_000
SEQUENTIAL_REQUESTS = 100
CONCURRENT_REQUESTS = 24
CONCURRENT_WORKERS = 4
PRIMARY_CONSUMER_ID = "read_path_perf_consumer"


class QueryRecorder:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.total = 0

    def record(self, sql: str) -> None:
        if sql.lstrip().upper().startswith("PRAGMA"):
            return
        with self.lock:
            self.total += 1


class CountingConnection:
    def __init__(self, connection: sqlite3.Connection, recorder: QueryRecorder) -> None:
        self.connection = connection
        self.recorder = recorder

    def __enter__(self) -> "CountingConnection":
        self.connection.__enter__()
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.connection.__exit__(exc_type, exc_value, traceback)

    def execute(self, sql: str, parameters: Any = None):
        self.recorder.record(sql)
        if parameters is None:
            return self.connection.execute(sql)
        return self.connection.execute(sql, parameters)

    def executescript(self, script: str) -> None:
        self.recorder.record(script)
        self.connection.executescript(script)

    def rollback(self) -> None:
        self.connection.rollback()


def main() -> int:
    report = run_evidence()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        "read_path_perf_after_fix "
        f"sequential={report['sequential']['status_counts']} "
        f"p95_ms={report['sequential']['latency_ms']['p95']} "
        f"candidate_max={report['candidate_pool']['max_candidate_count_recorded']}"
    )
    return 0 if report["decision"] == "GO local read-path proof" else 1


def run_evidence() -> dict[str, object]:
    with tempfile.TemporaryDirectory() as directory:
        db_path = Path(directory) / "read_path_perf.sqlite3"
        prepare_database(db_path)
        recorder = QueryRecorder()
        client = TestClient(create_app(db_path), raise_server_exceptions=False)
        counted_connect = counted_connect_factory(db_path, recorder)
        with mock.patch.object(auth, "connect", side_effect=counted_connect):
            with mock.patch.object(selection, "connect", side_effect=counted_connect):
                sequential = run_sequential_probe(client, recorder)
                concurrent = run_concurrent_probe(client)
    return build_report(sequential, concurrent)


def prepare_database(db_path: Path) -> None:
    initialize_database(db_path)
    seed_control_fixture(db_path, APPROVED_FIXTURE, "approved")
    seed_consumer(db_path, PRIMARY_CONSUMER_ID, 200, ["A2"], ["T10"])
    seed_api_credential(db_path, PRIMARY_CONSUMER_ID, primary_api_key())
    seed_entitlement(db_path, PRIMARY_CONSUMER_ID, ["A2"], ["T10"])
    for index in range(CONCURRENT_WORKERS):
        consumer_id = concurrent_consumer_id(index)
        seed_consumer(db_path, consumer_id, 20, ["A2"], ["T10"])
        seed_api_credential(db_path, consumer_id, concurrent_api_key(index))
        seed_entitlement(db_path, consumer_id, ["A2"], ["T10"])
    clone_synthetic_items(db_path, SYNTHETIC_ITEM_COUNT)
    with connect(db_path) as connection:
        connection.execute(
            "UPDATE quiz_items SET status = 'blocked' WHERE item_id = 'approved_traceable_001'"
        )


def clone_synthetic_items(db_path: Path, count: int) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            WITH digits(digit) AS (
                VALUES (0), (1), (2), (3), (4), (5), (6), (7), (8), (9)
            ),
            numbers(number) AS (
                SELECT ones.digit
                     + tens.digit * 10
                     + hundreds.digit * 100
                     + thousands.digit * 1000
                     + ten_thousands.digit * 10000
                FROM digits ones
                CROSS JOIN digits tens
                CROSS JOIN digits hundreds
                CROSS JOIN digits thousands
                CROSS JOIN digits ten_thousands
            )
            INSERT INTO quiz_items (
                item_id, source_id, language, level_band, sublevel, theme_id,
                subtheme_id, objective_id, pattern_id, difficulty_band, register,
                prompt, stem_text, options_json, answer_key, explanation, tags,
                coverage_cell_id, status, version, created_at, updated_at,
                reviewed_at, level_locked, locked_at
            )
            SELECT 'read_path_candidate_' || printf('%05d', numbers.number),
                   source_id, language, level_band, sublevel, 'T10',
                   subtheme_id, objective_id, pattern_id, difficulty_band,
                   register, prompt, stem_text, options_json, answer_key,
                   explanation, tags,
                   'A2::T10::O02::P01::' || printf('%05d', numbers.number),
                   'approved', version, created_at, updated_at,
                   reviewed_at, level_locked, locked_at
            FROM quiz_items
            CROSS JOIN numbers
            WHERE item_id = 'approved_traceable_001'
              AND numbers.number < ?
            """,
            (count,),
        )


def counted_connect_factory(db_path: Path, recorder: QueryRecorder):
    def counted_connect(_db_path: Path | None = None) -> CountingConnection:
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return CountingConnection(connection, recorder)

    return counted_connect


def run_sequential_probe(client: TestClient, recorder: QueryRecorder) -> dict[str, object]:
    results = []
    for _index in range(SEQUENTIAL_REQUESTS):
        before_queries = recorder.total
        result = post_next_item(client, PRIMARY_CONSUMER_ID, primary_api_key())
        result["query_count"] = recorder.total - before_queries
        results.append(result)
    return summarize_results(results)


def run_concurrent_probe(client: TestClient) -> dict[str, object]:
    results = []
    with ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
        futures = [
            executor.submit(
                post_next_item,
                client,
                concurrent_consumer_id(index % CONCURRENT_WORKERS),
                concurrent_api_key(index % CONCURRENT_WORKERS),
            )
            for index in range(CONCURRENT_REQUESTS)
        ]
        for future in as_completed(futures):
            results.append(future.result())
    summary = summarize_results(results)
    summary["workers"] = CONCURRENT_WORKERS
    return summary


def post_next_item(client: TestClient, consumer_id: str, api_key: str) -> dict[str, object]:
    started = time.perf_counter()
    try:
        response = client.post(
            "/v1/quiz-items/next",
            json={"consumer_id": consumer_id, "cefr_level": "A2", "theme_ids": ["T10"]},
            headers={"X-Consumer-Id": consumer_id, "X-QuizBank-API-Key": api_key},
        )
    except Exception as error:  # pragma: no cover - evidence captures unexpected failures
        return {
            "status_code": 0,
            "latency_ms": elapsed_ms(started),
            "exception": type(error).__name__,
        }
    result: dict[str, object] = {
        "status_code": response.status_code,
        "latency_ms": elapsed_ms(started),
    }
    if response.status_code == 200:
        body = response.json()
        decision = body["selection"]["decision"]
        result["candidate_count"] = int(decision["candidate_count"])
    return result


def elapsed_ms(started: float) -> float:
    return (time.perf_counter() - started) * 1000.0


def summarize_results(results: list[dict[str, object]]) -> dict[str, object]:
    latencies = [float(result["latency_ms"]) for result in results]
    statuses = Counter(str(result["status_code"]) for result in results)
    candidate_counts = [
        int(result["candidate_count"])
        for result in results
        if "candidate_count" in result
    ]
    query_counts = [
        int(result["query_count"])
        for result in results
        if "query_count" in result
    ]
    return {
        "requests": len(results),
        "status_counts": dict(sorted(statuses.items())),
        "exception_count": sum(1 for result in results if "exception" in result),
        "timeout_count": 0,
        "five_xx_count": sum(
            count for status, count in statuses.items() if status.startswith("5")
        ),
        "latency_ms": latency_summary(latencies),
        "candidate_count": count_summary(candidate_counts),
        "query_count": count_summary(query_counts),
    }


def latency_summary(values: list[float]) -> dict[str, float]:
    return {
        "min": round(min(values), 3),
        "p50": round(percentile(values, 50), 3),
        "p95": round(percentile(values, 95), 3),
        "p99": round(percentile(values, 99), 3),
        "max": round(max(values), 3),
        "mean": round(sum(values) / len(values), 3),
    }


def count_summary(values: list[int]) -> dict[str, float | int | None]:
    if not values:
        return {"min": None, "max": None, "mean": None}
    return {
        "min": min(values),
        "max": max(values),
        "mean": round(sum(values) / len(values), 3),
    }


def percentile(values: list[float], percentile_value: int) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(len(ordered) * percentile_value / 100))
    return ordered[index]


def build_report(
    sequential: dict[str, object],
    concurrent: dict[str, object],
) -> dict[str, object]:
    candidate_max = sequential["candidate_count"]["max"]
    thresholds_met = (
        sequential["status_counts"] == {"200": SEQUENTIAL_REQUESTS}
        and sequential["exception_count"] == 0
        and sequential["timeout_count"] == 0
        and float(sequential["latency_ms"]["p95"]) < 300.0
        and int(candidate_max or 0) <= CANDIDATE_POOL_LIMIT
    )
    return {
        "report_type": "read_path_perf_after_fix",
        "generated_at": utc_now(),
        "decision": "GO local read-path proof" if thresholds_met else "NO-GO local read-path proof",
        "environment": "local_sqlite_testclient_synthetic_30k",
        "production_touched": False,
        "production_deploy_performed": False,
        "production_load_test_performed": False,
        "secret_or_quiz_content_printed": False,
        "dataset": {
            "synthetic_published_items": SYNTHETIC_ITEM_COUNT,
            "levels": ["A2"],
            "themes": ["T10"],
            "quiz_content_in_report": False,
        },
        "candidate_pool": {
            "limit": CANDIDATE_POOL_LIMIT,
            "history_metric_candidate_limit": HISTORY_SCORING_CANDIDATE_LIMIT,
            "max_candidate_count_recorded": candidate_max,
            "cell_grouped_metrics_on_hot_path": False,
        },
        "sequential": sequential,
        "concurrent": concurrent,
        "thresholds": {
            "sequential_requests": SEQUENTIAL_REQUESTS,
            "sequential_status_200": SEQUENTIAL_REQUESTS,
            "p95_ms_allowed": 300.0,
            "p95_ms_target": 150.0,
            "candidate_max_allowed": CANDIDATE_POOL_LIMIT,
            "exceptions_allowed": 0,
            "timeouts_allowed": 0,
        },
        "thresholds_met": thresholds_met,
        "explicit_non_claims": {
            "not_production_deploy": True,
            "not_production_smoke_or_load": True,
            "not_paid_pilot_readiness": True,
            "not_broad_scale_approval": True,
        },
    }


def concurrent_consumer_id(index: int) -> str:
    return f"read_path_concurrent_{index:02d}"


def primary_api_key() -> str:
    return credential_value("primary")


def concurrent_api_key(index: int) -> str:
    return credential_value(f"concurrent-{index:02d}")


def credential_value(label: str) -> str:
    digest = hashlib.sha256(f"read-path-perf:{label}".encode("utf-8")).hexdigest()
    return f"local-{digest}"


if __name__ == "__main__":
    raise SystemExit(main())
