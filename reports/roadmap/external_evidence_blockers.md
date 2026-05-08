# Phase 7-9 External Evidence Blockers

Updated: 2026-05-08

This file lists blockers that cannot be closed by local repository work alone.
They must remain separate from local pre-pilot evidence.

## Phase 7 Closed Pilot Blockers

| Blocker | Required external evidence |
|---|---|
| Public/broader pilot environment | Protected public route exists for `api.valerchik.de`; broader beta/prod environment still needs owner approval and evidence boundary. |
| Telegram controlled send | Controlled direct real send succeeded after bot administrator access was confirmed and channel-compatible anonymous poll payload was used. Deployed worker real-send also succeeded for Public MVP / Protected Beta; production Telegram monitoring remains separate. |
| Closed external pilot smoke | End-to-end protected route scenario through the deployed runtime worker is recorded in `reports/beta/closed_external_pilot_smoke_2026-05-08.md`. Production-grade pilot monitoring and incident evidence remain separate. |
| Worker monitoring | Owner-reviewed VPS health/readiness evidence exists for Public MVP / Protected Beta; external dashboard or alert source still needed for production closure. |
| Automated pilot backup schedule | VPS backup timer is enabled and latest run succeeded; production monitored backup remains separate. |
| Production-like restore drill | Restore into isolated target using managed/pilot-like data beyond MVP SQLite and recorded result. |
| Support execution | Public MVP / Protected Beta contact gate is recorded; production SLA/support execution remains separate. |

## Phase 8 Public Beta Blockers

| Blocker | Required external evidence |
|---|---|
| Alerting cadence | Owner-reviewed Public MVP / Protected Beta monitoring evidence exists; production dashboard/alert source remains separate. |
| Controlled backup schedule | VPS backup timer is enabled and latest run succeeded; production monitored backup remains separate. |
| Release execution | App-level credential deploy, edge/app header split, protected public smoke and rollback drill are recorded; production rollback remains separate. |
| Public support/abuse path | Public GitHub support/abuse issue path exists; private owner security channel is recorded without secrets. |
| Beta legal/privacy review | Public MVP / Protected Beta review is approved; broad public beta, school, paid and production legal/privacy approval remain separate. |

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
