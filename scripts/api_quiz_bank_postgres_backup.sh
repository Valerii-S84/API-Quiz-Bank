#!/usr/bin/env sh
set -eu

POSTGRES_CONTAINER="${API_QUIZ_BANK_POSTGRES_CONTAINER:-api-quiz-bank-postgres}"
POSTGRES_DB="${API_QUIZ_BANK_POSTGRES_DB:-api_quiz_bank}"
POSTGRES_USER="${API_QUIZ_BANK_POSTGRES_USER:-api_quiz_bank}"
BACKUP_DIR="${API_QUIZ_BANK_BACKUP_DIR:-var/backups/api-quiz-bank}"

mkdir -p "$BACKUP_DIR"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_path="$BACKUP_DIR/api_quiz_bank_pg_$timestamp.dump"

docker exec "$POSTGRES_CONTAINER" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > "$backup_path"
test -s "$backup_path"
echo "postgres-backup-ok $backup_path"
