# Pilot Execution Checklist

Updated: 2026-05-08

Status: package prepared; pilot not executed.

## Checklist

| Item | Current status | Evidence now | Evidence required on server |
|---|---|---|---|
| Pilot environment named | not done | `docs/pilot_environment_requirements.md` | Environment id, owner and access boundary. |
| Pilot launch contract accepted | not done | `docs/pilot_launch_contract.md` | Signed/approved launch decision. |
| Health/readiness available | local only | local runtime tests and dry run | `/health` and `/ready` output from pilot environment. |
| Consumer lifecycle control | local only | pre-pilot dry run | active -> suspended -> blocked -> active evidence from pilot environment. |
| Delivery/repeat/quota behavior | local only | pre-pilot dry run | delivery, repeat denial and quota denial from pilot environment. |
| Telegram dry-run | not done | Telegram controlled-send runbook | Dry-run payload and compatibility result from pilot environment. |
| Telegram controlled real send | not done | Telegram controlled-send runbook | Approval record and send/failure evidence, only if approved. |
| Backup execution | local only | local restore report and operational runbook | Pilot backup metadata. |
| Restore drill | local only | local restore report | Restore drill against isolated pilot-like target. |
| Monitoring/alerts | not done | monitoring runbook and observability contract | Dashboard, alert or owner-review record. |
| Support path | package only | support and incident runbooks | Named reachable support/security channel. |
| Rollback path | tabletop only | rollback runbook/tabletop | Pilot rollback/disable execution or drill evidence. |
| Go/no-go decision | not done | go/no-go matrix template | Completed owner decision. |

## Rule

No checklist item that needs server, external service or owner approval is
closed by this package alone.
