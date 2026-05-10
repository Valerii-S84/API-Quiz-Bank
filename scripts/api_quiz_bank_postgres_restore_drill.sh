#!/usr/bin/env sh
set -eu

POSTGRES_CONTAINER="${API_QUIZ_BANK_POSTGRES_CONTAINER:-api-quiz-bank-postgres}"
POSTGRES_DB="${API_QUIZ_BANK_POSTGRES_DB:-api_quiz_bank}"
POSTGRES_USER="${API_QUIZ_BANK_POSTGRES_USER:-api_quiz_bank}"
BACKUP_PATH="${API_QUIZ_BANK_POSTGRES_BACKUP_PATH:?set API_QUIZ_BANK_POSTGRES_BACKUP_PATH}"
DRILL_DB="${API_QUIZ_BANK_POSTGRES_DRILL_DB:-api_quiz_bank_restore_drill}"

docker exec "$POSTGRES_CONTAINER" dropdb -U "$POSTGRES_USER" --if-exists "$DRILL_DB"
docker exec "$POSTGRES_CONTAINER" createdb -U "$POSTGRES_USER" "$DRILL_DB"
docker exec -i "$POSTGRES_CONTAINER" pg_restore -U "$POSTGRES_USER" -d "$DRILL_DB" < "$BACKUP_PATH"

docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$DRILL_DB" -v ON_ERROR_STOP=1 -t -A <<'SQL' >/tmp/api_quiz_bank_pg_restore_check.txt
SELECT COUNT(*) >= 5
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
    'quiz_items',
    'consumers',
    'entitlements',
    'deliveries',
    'selection_decisions'
  );
SQL

if [ "$(cat /tmp/api_quiz_bank_pg_restore_check.txt)" != "t" ]; then
  echo "postgres restore drill missing runtime tables" >&2
  exit 1
fi

echo "postgres-restore-drill-ok $DRILL_DB"
