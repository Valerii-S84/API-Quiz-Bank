# Pilot Launch Runbook

Status: future controlled pilot launch runbook; not executed.

## Scope

This runbook describes the future pilot execution sequence. It must not be read
as permission to create a server, deploy, or perform Telegram real send.

## 1. Preflight

1. Confirm pilot owner, runtime operator, Telegram operator and support owner.
2. Record target environment name and access boundary.
3. Record Git commit SHA, migration version and release notes.
4. Confirm no secret is committed or printed.
5. Confirm raw CSV is not a consumer-facing runtime input.
6. Confirm known limitations are listed.

Required evidence:

- environment identity record;
- owner list;
- version record;
- limitation note.

## 2. Environment Readiness

1. Run health check.
2. Run readiness check.
3. Confirm database dependency is ready.
4. Confirm migration version.
5. Confirm operator can view logs.

Required evidence:

- health output;
- readiness output;
- migration/version output;
- log source screenshot or text export with secrets redacted.

## 3. Consumer Control Check

1. Create or select pilot consumer.
2. Confirm active consumer can request eligible delivery.
3. Suspend consumer.
4. Confirm delivery is denied.
5. Block consumer if escalation is being tested.
6. Confirm delivery is denied.
7. Reactivate consumer only after owner approval.

Required evidence:

- active -> suspended -> blocked -> active status trace;
- denial response for suspended/blocked state;
- allowed response after reactivation;
- audit log rows with actor and reason.

## 4. Delivery Behavior Check

1. Request next eligible item for pilot consumer.
2. Confirm source traceability is present.
3. Confirm hidden answer behavior.
4. Repeat request and confirm repeat denial.
5. Use quota-limited consumer and confirm quota denial.

Required evidence:

- delivery id;
- delivery log;
- repeat denial reason;
- quota denial reason;
- item status and source traceability.

## 5. Backup and Restore Check

1. Run backup for pilot data store.
2. Record checksum/metadata.
3. Restore into isolated target.
4. Run readiness check against restored target.
5. Record result.

Required evidence:

- backup metadata;
- restore target;
- readiness result;
- owner sign-off.

## 6. Telegram Check

1. Execute Telegram dry-run first.
2. Review generated payload and compatibility result.
3. If approved, execute one controlled real send to approved target only.
4. Record send outcome and failure visibility.
5. Stop Telegram path if logging or cancellation is not observable.

Required evidence:

- dry-run payload summary;
- compatibility result;
- approval record if real send occurs;
- send result;
- failure/skip visibility.

## 7. Go/No-Go

1. Complete `reports/roadmap/pilot_go_no_go_matrix.md`.
2. Mark blockers.
3. Record owner decision.
4. If `no-go`, do not launch and open follow-up issues.
5. If `go`, launch only within approved scope.

## 8. Closeout

1. Store all evidence under `reports/`.
2. Update roadmap evidence register with server-side artifacts only.
3. Keep pilot gate open if any external evidence is missing.
4. Record rollback or incident actions if used.
