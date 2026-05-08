#!/usr/bin/env python3
"""Run an ephemeral PostgreSQL smoke test for the committed database contract."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
POSTGRES_IMAGE = "postgres:16-alpine"
DATABASE_NAME = "postgres"
DEFAULT_LOAD_PLAN_PATH = Path("reports/imports/control_sample_postgresql_load_plan.json")
DEFAULT_CANONICAL_INPUT_PATH = Path("data/imports/control_sample_items.jsonl")
DEFAULT_REPORT_PATH = Path("reports/imports/control_sample_postgresql_smoke.json")
DEFAULT_EXECUTED_AT = "2026-05-08T00:00:00+00:00"


class PostgreSQLSmokeError(RuntimeError):
    """Raised when the local PostgreSQL smoke cannot complete."""


def run_command(args: list[str], stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        check=True,
        input=stdin,
        text=True,
        capture_output=True,
    )


def read_json(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, str]]:
    rows = []
    for line in (ROOT / path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def sql_literal(value: object) -> str:
    if value is None:
        return "NULL"
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def nullable_timestamp(value: str) -> str:
    return "NULL" if value == "" else sql_literal(value)


def quiz_item_insert_sql(source_id: str, item: dict[str, str]) -> str:
    values = [
        item["item_id"],
        source_id,
        item["language"],
        item["level_band"],
        item["sublevel"],
        item["theme_id"],
        item["subtheme_id"],
        item["objective_id"],
        item["pattern_id"],
        item["difficulty_band"],
        item["register"],
        item["prompt"],
        item["stem_text"],
        f"{sql_literal(item['options'])}::jsonb",
        item["answer_key"],
        item["explanation"],
        item["tags"],
        item["coverage_cell_id"],
        item["status"],
        item["version"],
        item["created_at"],
        item["updated_at"],
        item["reviewed_at"],
        item["level_locked"],
        item["locked_at"],
    ]
    rendered = render_quiz_item_values(values)
    return f"INSERT INTO quiz_items VALUES ({rendered});"


def render_quiz_item_values(values: list[str]) -> str:
    rendered = [sql_literal(value) for value in values[:13]]
    rendered.append(values[13])
    rendered.extend(sql_literal(value) for value in values[14:22])
    rendered.append(nullable_timestamp(values[22]))
    rendered.append(sql_literal(values[23]))
    rendered.append(nullable_timestamp(values[24]))
    return ", ".join(rendered)


def source_insert_sql(row: dict[str, Any]) -> str:
    values = [
        row["source_id"],
        row["source_type"],
        row["provenance_note"],
        row["checksum_sha256"],
        row["status"],
        row["created_at"],
    ]
    return f"INSERT INTO sources VALUES ({', '.join(sql_literal(value) for value in values)});"


def import_batch_insert_sql(row: dict[str, Any]) -> str:
    values = [
        row["import_batch_id"],
        row["source_id"],
        row["parser_profile_id"],
        row["import_mode"],
        row["import_status"],
        row["source_checksum_sha256"],
        row["default_item_status"],
        row["row_count_detected"],
        row["accepted_candidate_count"],
        row["rejected_candidate_count"],
        row["report_uri"],
        row["started_at"],
        row["completed_at"],
        row["created_by"],
    ]
    return f"INSERT INTO import_batches VALUES ({', '.join(sql_literal(value) for value in values)});"


def import_batch_item_insert_sql(row: dict[str, Any]) -> str:
    values = [
        row["import_batch_id"],
        row["item_id"],
        row["source_id"],
        row["source_item_id"],
        row["source_row_number"],
        row["canonical_status"],
        row["content_hash_sha256"],
        row["created_at"],
    ]
    return f"INSERT INTO import_batch_items VALUES ({', '.join(sql_literal(value) for value in values)});"


def validation_result_insert_sql(row: dict[str, Any]) -> str:
    values = [
        row["validation_result_id"],
        row["import_batch_id"],
        row["source_id"],
        row["source_item_id"],
        row["source_row_number"],
        row["severity"],
        row["rule_id"],
        row["message"],
        row["created_at"],
    ]
    return f"INSERT INTO import_validation_results VALUES ({', '.join(sql_literal(value) for value in values)});"


def build_load_sql(plan: dict[str, Any], canonical_items: list[dict[str, str]]) -> str:
    tables = plan["tables"]
    source_id = str(plan["lineage"]["source_id"])
    statements = ["BEGIN;"]
    statements.extend(source_insert_sql(row) for row in tables["sources"])
    statements.extend(import_batch_insert_sql(row) for row in tables["import_batches"])
    statements.extend(quiz_item_insert_sql(source_id, item) for item in canonical_items)
    statements.extend(import_batch_item_insert_sql(row) for row in tables["import_batch_items"])
    statements.extend(validation_result_insert_sql(row) for row in tables["import_validation_results"])
    statements.append("COMMIT;")
    return "\n".join(statements) + "\n"


def start_container() -> str:
    if shutil.which("docker") is None:
        raise PostgreSQLSmokeError("docker_not_available")
    container_name = f"api-quiz-bank-pg-smoke-{uuid.uuid4().hex[:12]}"
    run_command(
        [
            "docker",
            "run",
            "--rm",
            "-d",
            "--name",
            container_name,
            "-e",
            "POSTGRES_PASSWORD=postgres",
            "-v",
            f"{ROOT / 'database' / 'postgresql'}:/schema:ro",
            POSTGRES_IMAGE,
        ]
    )
    return container_name


def wait_for_database(container_name: str) -> None:
    for _ in range(30):
        result = subprocess.run(
            ["docker", "exec", container_name, "pg_isready", "-U", "postgres", "-d", DATABASE_NAME],
            text=True,
            capture_output=True,
        )
        if result.returncode == 0:
            return
        time.sleep(1)
    raise PostgreSQLSmokeError("postgres_not_ready")


def psql(container_name: str, args: list[str], stdin: str | None = None) -> str:
    command = [
        "docker",
        "exec",
        "-i",
        container_name,
        "psql",
        "-v",
        "ON_ERROR_STOP=1",
        "-U",
        "postgres",
        "-d",
        DATABASE_NAME,
        *args,
    ]
    return run_command(command, stdin=stdin).stdout


def apply_schema(container_name: str) -> None:
    psql(container_name, ["-f", "/schema/001_create_runtime.sql"])
    psql(container_name, ["-f", "/schema/002_add_import_contract.sql"])


def query_scalar(container_name: str, sql: str) -> str:
    output = psql(container_name, ["-t", "-A", "-c", sql])
    return output.strip()


def smoke_counts(container_name: str) -> dict[str, int]:
    tables = [
        "sources",
        "import_batches",
        "quiz_items",
        "import_batch_items",
        "import_validation_results",
    ]
    return {table: int(query_scalar(container_name, f"SELECT COUNT(*) FROM {table};")) for table in tables}


def build_report(
    container_name: str,
    load_plan_path: Path,
    canonical_input_path: Path,
    executed_at: str,
) -> dict[str, Any]:
    counts = smoke_counts(container_name)
    lineage_join_count = int(
        query_scalar(
            container_name,
            """
            SELECT COUNT(*)
            FROM import_batch_items ibi
            JOIN import_batches ib
              ON ib.import_batch_id = ibi.import_batch_id
             AND ib.source_id = ibi.source_id
            JOIN quiz_items qi ON qi.item_id = ibi.item_id
            JOIN sources s ON s.source_id = ib.source_id;
            """,
        )
    )
    checksum_match = query_scalar(
        container_name,
        """
        SELECT bool_and(s.checksum_sha256 = ib.source_checksum_sha256)
        FROM sources s
        JOIN import_batches ib ON ib.source_id = s.source_id;
        """,
    )
    return {
        "report_type": "postgresql_contract_smoke",
        "executed_at": executed_at,
        "docker_image": POSTGRES_IMAGE,
        "database": DATABASE_NAME,
        "schema_files": [
            "database/postgresql/001_create_runtime.sql",
            "database/postgresql/002_add_import_contract.sql",
        ],
        "source_artifacts": {
            "load_plan_path": load_plan_path.as_posix(),
            "canonical_input_path": canonical_input_path.as_posix(),
        },
        "checks": {
            "schema_applied": True,
            "load_plan_applied": True,
            "counts": counts,
            "lineage_join_count": lineage_join_count,
            "source_checksum_match": checksum_match == "t",
        },
    }


def run_smoke(load_plan_path: Path, canonical_input_path: Path, report_path: Path, executed_at: str) -> None:
    plan = read_json(load_plan_path)
    canonical_items = read_jsonl(canonical_input_path)
    container_name = start_container()
    try:
        wait_for_database(container_name)
        apply_schema(container_name)
        psql(container_name, [], stdin=build_load_sql(plan, canonical_items))
        report = build_report(container_name, load_plan_path, canonical_input_path, executed_at)
    finally:
        subprocess.run(["docker", "stop", container_name], text=True, capture_output=True)
    write_report(report_path, report)


def write_report(path: Path, report: dict[str, Any]) -> None:
    output_path = ROOT / path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    output_path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local PostgreSQL contract smoke.")
    parser.add_argument("--load-plan", default=DEFAULT_LOAD_PLAN_PATH, type=Path)
    parser.add_argument("--canonical-input", default=DEFAULT_CANONICAL_INPUT_PATH, type=Path)
    parser.add_argument("--report-out", default=DEFAULT_REPORT_PATH, type=Path)
    parser.add_argument("--executed-at", default=DEFAULT_EXECUTED_AT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        run_smoke(args.load_plan, args.canonical_input, args.report_out, args.executed_at)
    except (PostgreSQLSmokeError, subprocess.CalledProcessError) as error:
        print(f"PostgreSQL contract smoke failed: {error}")
        return 1
    print(f"PostgreSQL contract smoke report written: {args.report_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
