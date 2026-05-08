# Pilot Go/No-Go Matrix

Updated: 2026-05-08

Status: go for local-only/internal closed pilot and protected public route
smoke; no-go for public beta, production or Telegram real send.

## Decision Matrix

| Area | Local package status | Current decision | Evidence required for go |
|---|---|---|---|
| Environment | local-only VPS plus protected public route identified | go for protected route smoke | Beta/prod environment remains out of scope. |
| Runtime readiness | VPS and protected public health/ready passed | go for protected route smoke | Beta/prod readiness remains out of scope. |
| Consumer lifecycle | VPS lifecycle evidence passed | go-local-only | Public/beta/prod execution remains out of scope. |
| Delivery behavior | VPS delivery/repeat/quota evidence passed | go-local-only | Public/beta/prod traffic remains out of scope. |
| Telegram | VPS dry-run passed and token secret wired | go-local-only dry-run; no-go for real send | Controlled send evidence only if explicitly approved later. |
| Backup/restore | VPS backup and restore drill passed | go-local-only | Automated/public beta backup remains out of scope. |
| Monitoring/alerts | owner-review cadence recorded | go-local-only | Dashboard or alert evidence remains required for broader launch. |
| Support/security | runbooks exist | no-go | Reachable support/security path and owner. |
| Rollback | disable path recorded | go-local-only | Executed deployment rollback remains out of scope. |
| Privacy/legal scope | baseline only | no-go if real personal data is in scope | Scope-specific review decision. |

## Current Decision

```text
GO for local-only/internal closed pilot.
NO-GO for public beta, production or Telegram real send.
Reason: local-only VPS environment, health/readiness, smoke, backup, restore
drill, lifecycle, delivery, repeat guard, quota denial, Telegram dry-run,
Telegram token secret wiring, protected public route smoke and ops cadence are
recorded; Telegram real send remains not approved/not done.
```

## Change Rule

Move any row toward `go` only after linking actual external evidence. Do not use
local docs, local SQLite proof, TestClient output or this matrix as substitute
for public, beta or production execution.
