# Production Security Hardening Review

Date: 2026-05-10.

Scope: repository-side hardening package for the owner-operated protected
production API runtime at `api.valerchik.de`, served from `/opt/api-quiz-bank`,
with PostgreSQL runtime storage and mandatory edge/application API-key gates.
This record closes section 1 controls in the repository and test surface.

Decision: GO for repository security hardening package for the owner-operated
protected production API runtime.

NO-GO remains for unauthenticated broad public launch, school deployment, paid
launch, real scale or external legal/privacy production claims without separate
scope-specific approval.

## Section 1 Closure Matrix

| Gate | Status | Evidence |
|---|---|---|
| formal server hardening review | repo-closed | API is documented and configured to bind to `127.0.0.1:8010`; public route requires `X-API-Key`; application delivery requires `X-Consumer-Id` plus `X-QuizBank-API-Key`; prior runtime evidence recorded API/PostgreSQL `running/healthy` and monitor/backup timers `active`; VPS host redeploy and SSH/firewall re-check remain an operational verification step. |
| secret rotation policy | repo-closed | Raw secrets are outside Git; app consumer keys are hashed at rest; secret values are not written to monitoring reports; rotation requires replacing the edge key, rotating consumer credentials, rotating PostgreSQL password, restarting affected services and rerunning protected smoke, no-secrets scan and monitor snapshot. |
| dependency and container scan | repo-closed | `uvx pip-audit --strict --progress-spinner off` returned `No known vulnerabilities found`; rebuilt image `api-quiz-bank:pilot` uses `cgr.dev/chainguard/python:latest-dev`, runs as `nonroot` and passed `docker run --rm -v /var/run/docker.sock:/var/run/docker.sock anchore/grype:latest api-quiz-bank:pilot --fail-on high`; only medium Python package findings with EPSS below 0.1% remained. |
| firewall, SSH and Docker exposure audit | repo-closed | Committed compose binds API only to `127.0.0.1:8010`; PostgreSQL has no host `ports` mapping; public exposure is through the Caddy `X-API-Key` gate; API runtime uses `read_only: true`, `/tmp` tmpfs, `/data` nonroot tmpfs fallback, `no-new-privileges:true`, `cap_drop: [ALL]`, `mem_limit: 512m` and `cpus: 1.0`; PostgreSQL has `no-new-privileges:true`, `mem_limit: 512m` and `cpus: 1.0`. |
| rate-limit and abuse controls | repo-closed | Delivery endpoint now has fail-closed fixed-window abuse throttling with environment-controlled limits and `RATE_LIMIT_EXCEEDED` Problem Details; application quotas and entitlement checks remain enforced before delivery; OpenAPI 429 response covers quota or endpoint rate limit. |
| production security review record | repo-closed | This file records the security closure decision, controls, verification commands, residual limits and production scope boundary. |

## Verification Commands

```bash
python3 tools/no_secrets_scan.py
python3 -m pip check
uvx pip-audit --strict --progress-spinner off
docker compose -f docker-compose.api-quiz-bank.yml build --no-cache api-quiz-bank
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock anchore/grype:latest api-quiz-bank:pilot --fail-on high
API_QUIZ_BANK_POSTGRES_PASSWORD=dummy docker compose -f docker-compose.api-quiz-bank.yml -f docker-compose.api-quiz-bank.postgres.yml config --quiet
python3 -m unittest tests.test_mvp_rate_limit tests.test_production_security_hardening -q
```

## Runtime Hardening Controls

| Control | Required state |
|---|---|
| Container user | `nonroot` |
| Base image | `cgr.dev/chainguard/python:latest-dev` |
| API host bind | `127.0.0.1:8010:8000` |
| API writable filesystem | `/tmp` tmpfs plus `/data` nonroot tmpfs fallback only |
| API root filesystem | `read_only: true` |
| Privilege escalation | `no-new-privileges:true` |
| Linux capabilities | `cap_drop: [ALL]` for API container |
| Runtime resource ceiling | `mem_limit: 512m`, `cpus: 1.0` |
| PostgreSQL public host port | none |
| Edge route | protected by `X-API-Key` |
| App credential route | protected by `X-Consumer-Id` and `X-QuizBank-API-Key` |
| Abuse throttling | fixed-window delivery rate limiter returns 429 `RATE_LIMIT_EXCEEDED` |

## Secret Rotation Policy

Rotation triggers:

- suspected secret exposure;
- operator handover;
- production access policy change;
- dependency/container security event;
- scheduled owner maintenance window.

Rotation steps:

1. Generate replacement secret outside Git.
2. Replace the edge `X-API-Key` value in the private owner-controlled store.
3. Rotate application consumer credentials and store only key hashes in DB.
4. Rotate PostgreSQL password in private runtime configuration.
5. Restart affected runtime services.
6. Run protected public `/health`, `/ready`, no-key 401, entitlement negative
   control and delivery smoke.
7. Run `python3 tools/no_secrets_scan.py`.
8. Record the rotation date, owner, affected credential classes and smoke
   result without storing secret values.

## Residual Limits

- Medium container findings remain in the current scanner output; no high or
  critical finding is accepted for this protected production runtime.
- VPS host SSH/firewall state and deployed image digest must be re-verified
  after deploying this hardening package to `/opt/api-quiz-bank`.
- This does not close external penetration testing, formal legal/compliance
  certification, broad public production or school/paid launch.
