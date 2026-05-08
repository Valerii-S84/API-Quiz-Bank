# Pilot Execution Checklist

Updated: 2026-05-08

Status: local-only/internal closed pilot evidence and protected public route
smoke recorded; public beta, production and deployed Telegram worker real send
not executed.

## Checklist

| Item | Current status | Evidence now | Evidence required on server |
|---|---|---|---|
| Pilot environment named | done for local-only VPS | `reports/pre_pilot/vps_local_only_pilot_evidence_2026-05-08.md` | New evidence required for public/beta/prod scope. |
| Pilot launch contract accepted | not done | `docs/pilot_launch_contract.md` | Signed/approved launch decision. |
| Health/readiness available | done for local-only VPS | `reports/pre_pilot/vps_local_only_pilot_evidence_2026-05-08.md` | Public/beta/prod scope remains out of scope. |
| Protected public route | done for `api.valerchik.de` smoke | `reports/pre_pilot/public_api_key_route_evidence_2026-05-08.md` | Beta/prod approval remains out of scope. |
| Consumer lifecycle control | done for local-only VPS | `reports/pre_pilot/vps_local_only_pilot_evidence_2026-05-08.md` | Public/beta/prod scope remains out of scope. |
| Delivery/repeat/quota behavior | done for local-only VPS | `reports/pre_pilot/vps_local_only_pilot_evidence_2026-05-08.md` | Public/beta/prod traffic remains out of scope. |
| Telegram dry-run | done for local-only VPS; local worker dry-run path added | `reports/pre_pilot/telegram_dry_run_readiness_2026-05-08.md`, `tools/run_telegram_delivery_smoke.py` | Deployed worker dry-run evidence required after merge/deploy. |
| Telegram token secret | wired on VPS | `reports/pre_pilot/telegram_secret_wiring_2026-05-08.md` | Rotate before production closure if required by owner. |
| Telegram controlled real send | direct send done; worker real-send not done | `reports/pre_pilot/telegram_controlled_send_2026-05-08.md`, Telegram controlled-send runbook | Approval record and worker send/failure evidence, only if approved. |
| Backup execution | done for local-only VPS | `reports/pre_pilot/vps_local_only_pilot_evidence_2026-05-08.md` | Automated/public beta backup metadata remains out of scope. |
| Restore drill | done for local-only VPS | `reports/pre_pilot/vps_local_only_pilot_evidence_2026-05-08.md` | Production-like managed DB restore remains out of scope. |
| Monitoring/alerts | owner-review cadence recorded | `reports/pre_pilot/vps_local_only_pilot_evidence_2026-05-08.md` | Dashboard or alert evidence required for broader launch. |
| Support path | package only | support and incident runbooks | Named reachable support/security channel. |
| Rollback path | disable path recorded | `reports/pre_pilot/vps_local_only_pilot_evidence_2026-05-08.md` | Deployment rollback execution remains out of scope. |
| Go/no-go decision | local-only/internal GO recorded | `reports/roadmap/pilot_go_no_go_matrix.md`, `reports/roadmap/phase_7_10_closure_decision_2026-05-08.md` | Owner approval required before broader launch. |

## Rule

No checklist item that needs server, external service or owner approval is
closed by this package alone.
