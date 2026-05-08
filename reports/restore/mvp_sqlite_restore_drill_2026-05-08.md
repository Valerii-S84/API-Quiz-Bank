# MVP SQLite Restore Drill Evidence

Date: 2026-05-08

Scope: local MVP SQLite backup/restore proof for Phase 7-8 local evidence.

This drill used an isolated database under ignored `var/phase_7_9_drill/` and
did not touch a production, pilot, beta or external environment.

## Commands

```bash
PYTHONPATH=src python3 -m quizbank_mvp.cli --db-path var/phase_7_9_drill/quizbank_mvp.sqlite3 init-db
PYTHONPATH=src python3 -m quizbank_mvp.cli --db-path var/phase_7_9_drill/quizbank_mvp.sqlite3 seed-demo
cp var/phase_7_9_drill/quizbank_mvp.sqlite3 var/phase_7_9_drill/quizbank_mvp_backup.sqlite3
cp var/phase_7_9_drill/quizbank_mvp_backup.sqlite3 var/phase_7_9_drill/restore_drill.sqlite3
QUIZBANK_DB_PATH=var/phase_7_9_drill/restore_drill.sqlite3 PYTHONPATH=src python3 - <<'PY'
from pathlib import Path
import hashlib
import sqlite3
from quizbank_mvp.database import database_is_ready

path = Path("var/phase_7_9_drill/restore_drill.sqlite3")
print("database_is_ready=", database_is_ready(path), sep="")
print(
    "backup_sha256=",
    hashlib.sha256(Path("var/phase_7_9_drill/quizbank_mvp_backup.sqlite3").read_bytes()).hexdigest(),
    sep="",
)
print("restore_size_bytes=", path.stat().st_size, sep="")
with sqlite3.connect(path) as connection:
    for table in ("quiz_items", "consumers", "entitlements"):
        count = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}_count={count}")
PY
```

## Result

```text
initialized database: /mnt/c/Users/User/Desktop/API Quiz Bank/var/phase_7_9_drill/quizbank_mvp.sqlite3
seeded MVP demo state
database_is_ready=True
backup_sha256=da08cfb61574197b75bff75b9300b20e1327c55193c9019dad033f49ad0d0dab
restore_size_bytes=77824
quiz_items_count=1
consumers_count=3
entitlements_count=2
```

## Limitation

This is local MVP restore evidence only. It does not satisfy pilot, beta or
production restore requirements for a managed database, monitored backup
schedule, recovery objective, access control or external environment.
