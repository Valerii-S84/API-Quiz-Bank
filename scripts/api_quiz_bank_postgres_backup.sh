#!/usr/bin/env sh
set -eu

POSTGRES_CONTAINER="${API_QUIZ_BANK_POSTGRES_CONTAINER:-api-quiz-bank-postgres}"
POSTGRES_DB="${API_QUIZ_BANK_POSTGRES_DB:-api_quiz_bank}"
POSTGRES_USER="${API_QUIZ_BANK_POSTGRES_USER:-api_quiz_bank}"
BACKUP_DIR="${API_QUIZ_BANK_BACKUP_DIR:-var/backups/api-quiz-bank}"
RETENTION_DAYS="${API_QUIZ_BANK_BACKUP_RETENTION_DAYS:-30}"
OFFSITE_DIR="${API_QUIZ_BANK_BACKUP_OFFSITE_DIR:-}"
ENCRYPTION_KEY_FILE="${API_QUIZ_BANK_BACKUP_ENCRYPTION_KEY_FILE:-}"
CREATED_BY="${API_QUIZ_BANK_BACKUP_CREATED_BY:-api-quiz-bank-postgres-backup}"

umask 077

is_non_negative_integer() {
  case "$1" in
    ''|*[!0-9]*)
      return 1
      ;;
    *)
      return 0
      ;;
  esac
}

sha256_file() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  else
    echo "unavailable"
  fi
}

cleanup_old_backups() {
  target_dir="$1"
  [ -d "$target_dir" ] || return 0
  if is_non_negative_integer "$RETENTION_DAYS"; then
    find "$target_dir" -type f \
      \( -name 'api_quiz_bank_pg_*.dump' \
      -o -name 'api_quiz_bank_pg_*.dump.enc' \
      -o -name 'api_quiz_bank_pg_*.dump.meta' \
      -o -name 'api_quiz_bank_pg_*.dump.enc.meta' \) \
      -mtime +"$RETENTION_DAYS" -exec rm -f {} \;
  fi
}

mkdir -p "$BACKUP_DIR"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_path="$BACKUP_DIR/api_quiz_bank_pg_$timestamp.dump"
backup_format="postgres-custom"
offsite_status="not-configured"

docker exec "$POSTGRES_CONTAINER" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > "$backup_path"
test -s "$backup_path"

if [ -n "$ENCRYPTION_KEY_FILE" ]; then
  if [ ! -r "$ENCRYPTION_KEY_FILE" ]; then
    echo "postgres backup encryption key file is not readable" >&2
    exit 1
  fi
  encrypted_path="$backup_path.enc"
  openssl enc -aes-256-cbc -salt -pbkdf2 \
    -pass "file:$ENCRYPTION_KEY_FILE" \
    -in "$backup_path" \
    -out "$encrypted_path"
  test -s "$encrypted_path"
  rm -f "$backup_path"
  backup_path="$encrypted_path"
  backup_format="postgres-custom+openssl-aes-256-cbc"
fi

size_bytes="$(wc -c < "$backup_path" | tr -d ' ')"
checksum_sha256="$(sha256_file "$backup_path")"
metadata_path="$backup_path.meta"
if [ -n "$OFFSITE_DIR" ]; then
  offsite_status="copied"
fi

cat >"$metadata_path" <<EOF
backup_id=api_quiz_bank_pg_$timestamp
environment=owner-operated-protected-production
database_name=$POSTGRES_DB
created_at_utc=$timestamp
backup_type=logical_dump
backup_format=$backup_format
size_bytes=$size_bytes
checksum_sha256=$checksum_sha256
retention_days=$RETENTION_DAYS
created_by=$CREATED_BY
storage_location=local:$backup_path
offsite_status=$offsite_status
restore_tested_status=pending
EOF

if [ -n "$OFFSITE_DIR" ]; then
  mkdir -p "$OFFSITE_DIR"
  cp "$backup_path" "$metadata_path" "$OFFSITE_DIR"/
fi

cleanup_old_backups "$BACKUP_DIR"
if [ -n "$OFFSITE_DIR" ]; then
  cleanup_old_backups "$OFFSITE_DIR"
fi

echo "postgres-backup-ok $backup_path"
