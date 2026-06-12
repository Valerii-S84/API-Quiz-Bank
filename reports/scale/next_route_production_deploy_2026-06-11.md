# Next Route Production Deploy - 2026-06-11

Status: `Partial`.

No production deploy, rebuild, restart, migration execution or smoke write was
performed in this pass.

## Intended Scope

Deploy only the `/v1/quiz-items/next` hot path fix and the required PostgreSQL
index migration for the owner-operated protected production API runtime at
`/opt/api-quiz-bank`.

## Rollback Plan Identified

| Item | Value |
|---|---|
| Server old SHA | `904babbd998adcf43cfbc7945d5f24d499ec47c4` |
| API image | `api-quiz-bank:pilot` |
| API container | `api-quiz-bank-pilot` |
| PostgreSQL container | `api-quiz-bank-postgres` |
| API restart before deploy | restart count `0` |
| PostgreSQL restart | not allowed and not planned |
| If smoke fails | stop smoke immediately, keep diagnostic credential revoked, restore previous code/image using the documented rollback process before any further load testing |

## Documented Deploy Path

`runbooks/server_deploy.md` documents a git-based update in `/opt/api-quiz-bank`
followed by Docker Compose rebuild/recreate. The running API container was
created with these compose files:

- `/opt/api-quiz-bank/docker-compose.api-quiz-bank.yml`
- `/opt/api-quiz-bank/docker-compose.api-quiz-bank.postgres.yml`
- `/opt/api-quiz-bank/docker-compose.api-quiz-bank.secrets.yml`

Secret file contents were not read or printed.

## Blocking Findings

| Finding | Result |
|---|---|
| Local hotfix SHA | `9cfdc8ebefa452bd41bb094726068379bca748ca` |
| Local hotfix branch | `codex/release-governance-evidence` |
| Local hotfix on local `origin/main` | no |
| Server branch/SHA | `main` / `904babbd998adcf43cfbc7945d5f24d499ec47c4` |
| Server worktree | dirty with 2 tracked non-hotfix files |
| Formal runbook command would deploy hotfix | no; hotfix is not on server `origin/main` |
| Manual patch/tree deploy path | not sufficiently documented for this risk level |

The dirty server files were:

- `src/quizbank_mvp/trusted_delivery.py`
- `tests/test_shorts_factory_backend.py`

The currently running API image already contains the runtime part of that dirty
trusted-delivery change, but the server worktree is still not a clean,
documented hotfix deployment base.

## Decision

Deployment stopped before any production write. This is `Partial`, not `Done`,
because applying the fix would require either pushing/merging the hotfix through
the repository flow or using an ad hoc tree/patch deployment path. The task
explicitly forbids an unclear or chaotic manual deploy.

## Post-Stop Production State

| Check | Result |
|---|---|
| API container | `running/healthy`, restart count `0` after stop decision |
| PostgreSQL container | `running/healthy`, restart count `0` after stop decision |
| Local health/ready | `200` / `200` after stop decision |
| Protected public health/ready | `200` / `200` after stop decision |
| Index migration applied | no |
| Production code changed | no |
| Diagnostic consumer created | no |
| Credential created/revoked | not created |
| Full staged load test | not run |
