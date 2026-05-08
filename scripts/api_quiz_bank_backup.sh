#!/usr/bin/env sh
set -eu

DB_PATH="${QUIZBANK_DB_PATH:-var/api-quiz-bank/quizbank_mvp.sqlite3}"
BACKUP_DIR="${API_QUIZ_BANK_BACKUP_DIR:-var/backups/api-quiz-bank}"

if [ ! -f "$DB_PATH" ]; then
  echo "database not found: $DB_PATH" >&2
  exit 1
fi

mkdir -p "$BACKUP_DIR"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_path="$BACKUP_DIR/quizbank_mvp_$timestamp.sqlite3"

cp "$DB_PATH" "$backup_path"
python3 - "$backup_path" <<'PY'
import sqlite3
import sys

path = sys.argv[1]
with sqlite3.connect(path) as connection:
    result = connection.execute("PRAGMA integrity_check").fetchone()[0]
if result != "ok":
    raise SystemExit(f"backup integrity check failed: {result}")
print(f"backup-ok {path}")
PY
