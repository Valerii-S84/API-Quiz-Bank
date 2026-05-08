# Pilot Launch Contract

Status: future controlled pilot launch contract; no pilot launched.

## Scope

This contract defines what must be true before API Quiz Bank may run a closed
pilot. It does not authorize deploy, server creation or Telegram real send by
itself.

## Allowed Pilot Claim

Allowed only after external evidence exists:

```text
Closed pilot is running in a named controlled environment with approved scope,
observable delivery, backup/restore path, support path and rollback path.
```

Not allowed from this package alone:

```text
pilot gate done
public beta ready
production ready
Telegram real delivery proven
```

## Launch Roles

| Role | Responsibility |
|---|---|
| Pilot owner | Final go/no-go, launch window, scope and evidence ownership. |
| Runtime operator | Health/readiness, deploy state, rollback and service stop/start path. |
| Data owner | Pilot item eligibility, source traceability and status rules. |
| Telegram operator | Dry-run or controlled send protocol and send evidence. |
| Support owner | Issue intake, consumer communication and escalation. |
| Security/privacy owner | Private issue path, sensitive-data handling and review limits. |

## Entry Criteria

- Named pilot environment exists.
- Pilot owner and operators are assigned.
- Current Git commit and migration version are recorded.
- Health/readiness checks pass in the pilot environment.
- Consumer lifecycle control is tested in the pilot environment.
- Delivery/repeat/quota behavior is tested in the pilot environment.
- Backup has run and restore drill is recorded.
- Monitoring/alerts or owner review cadence exists.
- Telegram dry-run or approved controlled send is ready if Telegram is in scope.
- Support and incident path are reachable.
- Known limitations are recorded.

## Exit Criteria

Pilot launch contract is satisfied only when:

- go/no-go matrix says `go`;
- no P0 blocker remains open;
- rollback path is named and tested for pilot scope;
- launch evidence is stored under `reports/`;
- external gates in the roadmap evidence register are updated with actual
  server-side evidence.

## Stop Conditions

Stop or no-go if any of these are true:

- environment identity or owner is missing;
- raw CSV is exposed directly to a consumer;
- draft, blocked or retired item can be delivered;
- consumer suspension/block path fails;
- backup is missing or restore path is untested;
- Telegram send cannot be observed or safely cancelled;
- private support/security path is missing;
- legal/privacy review blocks the selected pilot scope.

## Evidence Boundary

This contract is a readiness artifact. It must be paired with server-side
execution evidence before any pilot gate can move from open to closed.
