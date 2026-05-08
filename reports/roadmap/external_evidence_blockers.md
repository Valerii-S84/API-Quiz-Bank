# Phase 7-9 External Evidence Blockers

Updated: 2026-05-08

This file lists blockers that cannot be closed by local repository work alone.
They must remain separate from local pre-pilot evidence.

## Phase 7 Closed Pilot Blockers

| Blocker | Required external evidence |
|---|---|
| Public/broader pilot environment | Protected public route exists for `api.valerchik.de`; broader beta/prod environment still needs owner approval and evidence boundary. |
| Telegram controlled send | Controlled real send succeeded after bot administrator access was confirmed and channel-compatible anonymous poll payload was used. Runtime worker delivery id remains separate because worker path is not implemented. |
| Worker monitoring | Owner-reviewed VPS health/readiness evidence exists; external dashboard or alert source still needed for beta/prod closure. |
| Automated pilot backup schedule | VPS backup timer is enabled and latest run succeeded; production monitored backup remains separate. |
| Production-like restore drill | Restore into isolated target using managed/pilot-like data beyond MVP SQLite and recorded result. |
| Support execution | Named support channel and at least one issue/containment record. |

## Phase 8 Public Beta Blockers

| Blocker | Required external evidence |
|---|---|
| Alerting cadence | Owner-reviewed VPS evidence exists; alert source, formal owner review cadence or dashboard evidence still needed. |
| Controlled backup schedule | VPS backup timer is enabled and latest run succeeded; production monitored backup remains separate. |
| Release execution | App-level credential deploy, edge/app header split and protected public smoke are recorded; rollback execution remains limited to disable/tabletop evidence. |
| Public support/abuse path | Public GitHub support/abuse issue path exists; signed/private security contact remains unresolved. |
| Beta legal/privacy review | Scope-specific completed review in `reports/compliance/legal_review_record.md`. |

## Phase 9 Production Blockers

| Blocker | Required external evidence |
|---|---|
| Controlled deployment | Production deployment target, owner and CI/CD or approved deployment process. |
| Monitored backups | Production backup monitor or owner-reviewed backup evidence. |
| Production restore drill | Recorded restore drill for production-like data and target. |
| Monitoring dashboard | Dashboard or equivalent operational review surface. |
| Critical alerts | Alert policy or formal owner review process. |
| Incident drill | Production incident owner and drill/playbook execution record. |
| Rollback execution | Verified rollback path for deployment, data and disable/containment actions. |
| Production privacy/legal approval | Launch approval and privacy/legal review appropriate to production scope. |

## Guardrail

None of these blockers may be marked `Done` from local docs, SQLite evidence,
TestClient responses or CI-only checks.
