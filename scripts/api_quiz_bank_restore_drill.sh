#!/usr/bin/env sh
set -eu

DB_PATH="${QUIZBANK_DB_PATH:-var/api-quiz-bank/quizbank_mvp.sqlite3}"
DRILL_DIR="${API_QUIZ_BANK_RESTORE_DRILL_DIR:-var/restore-drills/api-quiz-bank}"

if [ ! -f "$DB_PATH" ]; then
  echo "database not found: $DB_PATH" >&2
  exit 1
fi

mkdir -p "$DRILL_DIR"
restore_path="$DRILL_DIR/restore_drill.sqlite3"
cp "$DB_PATH" "$restore_path"

python3 - "$restore_path" <<'PY'
import sqlite3
import sys

path = sys.argv[1]
with sqlite3.connect(path) as connection:
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
required = {"quiz_items", "consumers", "entitlements", "deliveries", "audit_log"}
missing = sorted(required - tables)
if integrity != "ok":
    raise SystemExit(f"restore integrity check failed: {integrity}")
if missing:
    raise SystemExit(f"restore missing tables: {', '.join(missing)}")
print(f"restore-drill-ok {path}")
PY
