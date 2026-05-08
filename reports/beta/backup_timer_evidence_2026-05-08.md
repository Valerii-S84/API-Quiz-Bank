# Backup Timer Evidence

Date: 2026-05-08

Scope: live VPS pilot backup cadence for the SQLite beta/pilot datastore.

## Systemd Timer

| Check | Result |
|---|---|
| Unit | `api-quiz-bank-backup.timer` |
| Enabled | yes |
| Active | yes |
| Schedule | daily at `03:20 UTC` |
| Next run | `2026-05-09 03:20:00 UTC` |
| Service | `api-quiz-bank-backup.service` |
| Latest service result | `success` |

## Manual Trigger

```text
backup-ok /var/backups/api-quiz-bank/quizbank_mvp_20260508T121158Z.sqlite3
```

## Boundary

This closes a controlled VPS SQLite backup cadence for beta/pilot evidence. It
does not close production monitored backups or production-like PostgreSQL
restore requirements.
