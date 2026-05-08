# Pilot Go/No-Go Matrix

Updated: 2026-05-08

Status: no-go until external pilot evidence exists.

## Decision Matrix

| Area | Local package status | Current decision | Evidence required for go |
|---|---|---|---|
| Environment | requirements written | no-go | Named pilot environment and owner. |
| Runtime readiness | local proof only | no-go | Health/readiness from pilot environment. |
| Consumer lifecycle | local proof only | no-go | Active/suspended/blocked/reactivated evidence on pilot server. |
| Delivery behavior | local proof only | no-go | Delivery, repeat denial and quota denial from pilot server. |
| Telegram | protocol written | no-go | Dry-run evidence, plus controlled send evidence only if approved. |
| Backup/restore | protocol written, local drill exists | no-go | Pilot backup and isolated restore drill evidence. |
| Monitoring/alerts | protocol written | no-go | Dashboard, alert or owner-review cadence evidence. |
| Support/security | runbooks exist | no-go | Reachable support/security path and owner. |
| Rollback | tabletop exists | no-go | Pilot rollback or disable drill evidence. |
| Privacy/legal scope | baseline only | no-go if real personal data is in scope | Scope-specific review decision. |

## Current Decision

```text
NO-GO for pilot execution.
Reason: this repository contains the pilot execution package, but no named
pilot environment or server-side evidence exists yet.
```

## Change Rule

Move any row toward `go` only after linking actual external evidence. Do not use
local docs, local SQLite proof, TestClient output or this matrix as substitute
for pilot-environment execution.
