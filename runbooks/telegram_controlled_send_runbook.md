# Telegram Controlled Send Runbook

Status: protocol for future controlled send; no Telegram send executed.

## Scope

This runbook defines the dry-run and controlled real-send protocol for a future
pilot. It does not authorize a real Telegram send in the current repository
state.

## Required Preconditions

- Telegram consumer exists in governed runtime state.
- Consumer status is active.
- Entitlement and quota are valid.
- Selected item is approved or published for pilot scope.
- Payload passes Telegram compatibility validation.
- Bot token is stored outside Git.
- Target chat/channel is approved for controlled pilot.
- Operator and approver are named.
- Rollback/disable path is ready.

## Dry-Run Protocol

1. Request delivery through API/selection path.
2. Build Telegram payload without sending it.
3. Validate option count, text length, answer visibility and parse mode.
4. Record delivery id or dry-run attempt id.
5. Record selected item id, status and source traceability.
6. Record whether send would be skipped, sent or blocked.

Required evidence:

- dry-run timestamp;
- consumer id;
- item id and status;
- payload compatibility result;
- skip/send decision;
- redacted log excerpt.

## Controlled Real Send Protocol

Real send is allowed only after dry-run review and explicit approval.

1. Confirm target chat/channel.
2. Confirm target audience is closed pilot only.
3. Confirm no secret or private token will be logged.
4. Send one approved payload.
5. Record Telegram message id or failure reason.
6. Record delivery status as sent, failed, skipped or cancelled.
7. Confirm failure/skip appears in monitoring or owner-review artifact.

## Abort Conditions

- Target is ambiguous or public.
- Payload includes hidden answer before authorized reveal.
- Consumer is suspended or blocked.
- Item status is draft, blocked or retired.
- Logging is unavailable.
- Bot token or target identifier would be printed in public artifact.
- Operator cannot disable the consumer/channel.

## Required Server-Side Evidence

- approval record;
- dry-run payload summary;
- compatibility result;
- controlled send result if real send is approved;
- delivery/attempt log;
- failure visibility evidence;
- rollback/disable evidence if abort path is exercised.

## Non-Closure Rule

This runbook does not close Telegram pilot readiness. Telegram pilot readiness
requires execution evidence from the real pilot environment.
