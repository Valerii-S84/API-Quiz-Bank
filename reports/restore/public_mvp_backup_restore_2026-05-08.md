# Public MVP / Protected Beta Backup and Restore Evidence

Date: 2026-05-08

Scope: protected VPS SQLite runtime at `/opt/api-quiz-bank`. This is not a
production PostgreSQL or managed-database restore drill.

## Timer Evidence

| Check | Result |
|---|---|
| Timer unit | `api-quiz-bank-backup.timer` |
| Active | `active` |
| Enabled | `enabled` |
| Backup path | `/var/backups/api-quiz-bank` |
| Runtime DB path | `/opt/api-quiz-bank/var/api-quiz-bank/quizbank_mvp.sqlite3` |
| Owner | project owner / authorized VPS operator |

## Executed Evidence

| Step | Result |
|---|---|
| Pre-drill backup | `backup-ok /var/backups/api-quiz-bank/quizbank_mvp_20260508T183943Z.sqlite3` |
| Pre-drill restore | `restore-drill-ok /var/backups/api-quiz-bank/restore-drills/20260508T183943Z_public_mvp_6_10/restore_drill.sqlite3` |
| Recovery backup | `backup-ok /var/backups/api-quiz-bank/quizbank_mvp_20260508T184051Z.sqlite3` |
| Recovery restore | `restore-drill-ok /var/backups/api-quiz-bank/restore-drills/20260508T184051Z_public_mvp_6_10_recovery/restore_drill.sqlite3` |
| Rollback drill backup | `backup-ok /var/backups/api-quiz-bank/quizbank_mvp_20260508T184120Z.sqlite3` |
| Rollback drill restore | `restore-drill-ok /var/backups/api-quiz-bank/restore-drills/20260508T184120Z_public_mvp_rollback_success/restore_drill.sqlite3` |

## Decision

```text
GO for Public MVP / Protected Beta SQLite backup/restore gate
NO-GO for production managed database backup/restore
```

## Boundary

The restore drills used isolated restore targets under
`/var/backups/api-quiz-bank/restore-drills/`. The active runtime database was
not overwritten by a restore drill.
