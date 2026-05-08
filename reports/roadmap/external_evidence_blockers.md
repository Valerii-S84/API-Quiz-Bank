# Phase 7-9 External Evidence Blockers

Updated: 2026-05-08

This file lists blockers that cannot be closed by local repository work alone.
They must remain separate from local pre-pilot evidence.

## Phase 7 Closed Pilot Blockers

| Blocker | Required external evidence |
|---|---|
| Public/broader pilot environment | Protected public route exists for `api.valerchik.de`; broader beta/prod environment still needs owner approval and evidence boundary. |
| Telegram controlled send | Executed dry-run log or controlled real send evidence with failure visibility after explicit approval. |
| Worker monitoring | API/worker log source or dashboard showing delivery failures and denials. |
| Automated pilot backup schedule | Automated or independently reviewed backup mechanism beyond manual local-only VPS evidence. |
| Production-like restore drill | Restore into isolated target using managed/pilot-like data beyond MVP SQLite and recorded result. |
| Support execution | Named support channel and at least one issue/containment record. |

## Phase 8 Public Beta Blockers

| Blocker | Required external evidence |
|---|---|
| Alerting cadence | Alert source, owner review cadence or dashboard evidence. |
| Controlled backup schedule | Automated or reliably controlled backup schedule for beta data. |
| Release execution | Completed release/rollback checklist for beta scope. |
| Public support/abuse path | User-visible support, abuse and security contact path. |
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
