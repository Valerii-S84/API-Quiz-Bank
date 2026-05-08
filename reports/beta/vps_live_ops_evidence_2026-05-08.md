# VPS Live Operations Evidence

Date: 2026-05-08

Scope: live VPS pilot runtime checks without deploy, schema change or secret
disclosure.

## Runtime Health

| Check | Result |
|---|---|
| Container health | `running/healthy` |
| Host bind | `127.0.0.1:8010` |
| Local health | `200 {"status":"ok","service":"api-quiz-bank","version":"0.1.0"}` |
| Local readiness | `200 {"status":"ok","checks":[{"name":"database","status":"ok"}]}` |

## Backup / Restore

| Check | Result |
|---|---|
| Backup command | `backup-ok /var/backups/api-quiz-bank/quizbank_mvp_20260508T112742Z.sqlite3` |
| Backup size | `77824` bytes |
| Restore drill command | `restore-drill-ok /var/lib/api-quiz-bank/restore-drills/restore_drill.sqlite3` |

## Boundary

This proves live pilot SQLite backup and restore-drill mechanics only. It is not
a production-like PostgreSQL restore drill and does not prove an automated beta
backup schedule.
