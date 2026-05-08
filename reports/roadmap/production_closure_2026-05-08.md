# Production Closure Record

Date: 2026-05-08

Scope: roadmap step 12 / `docs/14_roadmap.md` section 19 production readiness.

## Decision

```text
NO-GO production
```

The VPS at `/opt/api-quiz-bank` was cleanly fast-forwarded, rebuilt and smoke
tested as the protected API runtime. This record does not promote that VPS to
the production target.

## Clean Deploy Evidence

```text
host=ubuntu-8gb-nbg1-1
path=/opt/api-quiz-bank
branch=main
head=78c899ddb996c64c1ee67f4d9feb29eea55f27da
origin_main=78c899ddb996c64c1ee67f4d9feb29eea55f27da
image=sha256:b8df89fa3250b8d87171d6521bb894dd409832e6c66657a0f3731b5b69602831
container=/api-quiz-bank-pilot
state=running/healthy
restart_count=0
started_at=2026-05-08T15:44:40.275495572Z
port=127.0.0.1:8010
tracked_worktree=clean
server_only_untracked=docker-compose.api-quiz-bank.secrets.yml, docker-compose.api-quiz-bank.yml.bak_20260508T084341Z
```

Server-only secrets and overrides were not printed or copied.

## Verification

```text
health -> 200
ready -> 200
app smoke -> smoke-ok
backup -> backup-ok /var/backups/api-quiz-bank/quizbank_mvp_20260508T154554Z.sqlite3
restore drill -> restore-drill-ok /var/backups/api-quiz-bank/restore-drills/20260508T154554Z_roadmap_11_14/restore_drill.sqlite3
backup timer -> active
protected public route -> health/ready 200, no-edge 401, missing app credential 401, next item 200, delivery read 200, repeat 404, quota 429, entitlement 403, suspended 403
isolated PostgreSQL contract smoke -> schema_applied=true, load_plan_applied=true, lineage_join_count=2
```

## Target Decision

```text
The current VPS remains a protected API runtime. It is not promoted to the
production target by this closure pass.
```

## Remaining Production Gates

- persistent production database is not recorded;
- external production monitoring/dashboard or alert source is not recorded;
- full deployment rollback execution is not recorded;
- production privacy/legal launch approval is not recorded;
- final production launch approval is not recorded.

## Operational Note

After clean checkout, `./scripts/api_quiz_bank_smoke.sh` returned
`Permission denied` because the committed shell scripts are not executable in
Git. The smoke was executed successfully with `sh scripts/api_quiz_bank_smoke.sh`.

Repository remediation:

```text
scripts/api_quiz_bank_backup.sh -> Git mode 100755
scripts/api_quiz_bank_restore_drill.sh -> Git mode 100755
scripts/api_quiz_bank_smoke.sh -> Git mode 100755
```

This fixes the clean-checkout script execution defect for the next committed
deploy path. The already-running VPS was not redeployed again for this
file-mode-only remediation.
