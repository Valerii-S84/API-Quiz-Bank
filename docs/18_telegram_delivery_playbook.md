# API Quiz Bank — Telegram Delivery Playbook

**Документ:** `docs/18_telegram_delivery_playbook.md`  
**Назва проєкту:** API Quiz Bank  
**Внутрішня історична назва:** QuizBank / German QuizBank Platform  
**Версія:** 1.0.0  
**Статус:** practical Telegram delivery playbook and channel-operations workflow; subordinate to `CONSTITUTION.md`; aligned with `00_vision.md`–`17_admin_workflow.md`  
**Дата:** 2026-05-07  
**Мова:** українська з канонічними технічними термінами англійською  
**Власник:** project owner / authorized Telegram delivery maintainer  
**Керівні документи:** `CONSTITUTION.md`, `docs/02_requirements_srs.md`, `docs/03_use_cases.md`, `docs/04_domain_model.md`, `docs/05_architecture.md`, `docs/08_security_threat_model.md`, `docs/09_quality_assurance.md`, `docs/10_operations.md`, `docs/13_stanford_presentation_outline.md`, `docs/14_roadmap.md`, `docs/17_admin_workflow.md`  
**Наступні документи:** `19_privacy_compliance.md`

---

## 0. Executive Summary

`18_telegram_delivery_playbook.md` визначає, як Telegram channel/bot delivery має працювати як керований consumer path, а не як окремий самодостатній бот з прихованою логікою selection, billing або corpus access.

Головна теза документа:

```text
Telegram is a delivery adapter, not a source of truth.
```

У цьому проєкті правильний Telegram path виглядає так:

```text
schedule
  → authorized worker
  → consumer config load
  → API/selection request
  → status/entitlement/repeat/compatibility checks
  → Telegram payload build
  → send or dry-run
  → delivery log
  → analytics and operations visibility
```

Неправильний path:

```text
bot reads raw CSV
  → picks random item
  → ignores status/repeat/quota
  → posts directly
  → no delivery log
  → no operational traceability
```

Final rule:

```text
No Telegram delivery may bypass canonical selection, consumer rules,
compatibility validation, delivery logging or incident visibility.
```

---

## 1. Role of This Document

### 1.1. Мета документа

`18_telegram_delivery_playbook.md` відповідає на питання:

```text
Як Telegram worker взаємодіє з schedule, API and selection engine?
Які preflight checks потрібні до реального channel posting?
Як Telegram compatibility validated before send?
Що робити при no-eligible, send failure, duplicate risk or quota denial?
Як виглядають dry-run, simulated delivery and demo-safe modes?
Які logs, metrics and audit/evidence are mandatory?
```

### 1.2. Місце в документаційній ієрархії

```text
CONSTITUTION.md
  ↓
docs/02_requirements_srs.md
  ↓
docs/03_use_cases.md
  ↓
docs/04_domain_model.md
  ↓
docs/05_architecture.md
  ↓
docs/08_security_threat_model.md
  ↓
docs/09_quality_assurance.md
  ↓
docs/10_operations.md
  ↓
docs/17_admin_workflow.md
  ↓
docs/18_telegram_delivery_playbook.md
```

### 1.3. Що цей документ робить

Цей документ визначає:

```text
Telegram delivery runtime model
worker responsibilities
preflight and launch gate
compatibility validation
schedule/repeat/idempotency rules
send-failure handling
dry-run and simulated delivery modes
channel pause/disable paths
metrics, logs and QA hooks
demo-safe Telegram proof contract
```

### 1.4. Що цей документ не робить

Цей документ НЕ є:

```text
Telegram Bot API reference;
selection-engine architecture replacement;
admin workflow replacement;
privacy/legal policy replacement;
full chatbot conversation design.
```

---

## 2. Telegram Delivery Thesis

### 2.1. Consumer thesis

Telegram channel or bot is a governed consumer type that receives content from the platform core under the same rules as API, web or demo consumers.

### 2.2. Adapter thesis

Telegram worker converts canonical quiz delivery into Telegram-compatible payloads. It must not own content truth, status truth, billing truth or repeat truth.

### 2.3. Pilot thesis

Real Telegram posting begins only after compatibility, logging, idempotency and negative controls are demonstrable.

---

## 3. Non-Negotiable Telegram Rules

1. Telegram worker MUST obtain quiz items through API/selection engine, never by reading raw CSV.
2. Telegram worker MUST deliver only approved/published items according to consumer and environment rules.
3. Telegram compatibility MUST be validated before send.
4. Telegram delivery MUST respect consumer status, entitlement, quota, schedule and repeat policy.
5. Telegram send result MUST be logged as success, failure, skipped, dry-run or cancelled.
6. Telegram path MUST support safe dry-run or simulated mode before real channel posting.
7. Telegram adapter MUST NOT leak hidden correct-answer information outside authorized worker-to-Telegram flow.

---

## 4. Runtime Model

### 4.1. Core components

Telegram delivery path SHOULD use or emulate:

```text
delivery_schedule
scheduler
Telegram worker
API/selection engine
consumer configuration
repeat policy
compatibility validator
Telegram adapter
delivery log
analytics/operations monitor
```

### 4.2. Responsibility boundaries

| Component | Responsibility |
|---|---|
| Scheduler | Triggers due posting job for a specific Telegram consumer |
| Telegram worker | Orchestrates request, validation, send/dry-run and logging |
| API/Selection engine | Selects eligible item under status, entitlement, repeat and compatibility rules |
| Telegram adapter | Builds Telegram-specific payload and executes send |
| Delivery log | Records attempt, outcome, identifiers and reasons |
| Operations/admin | Pause, disable, inspect, rerun or block when needed |

### 4.3. Boundary rule

Telegram worker may orchestrate delivery, but it must never replace selection logic, corpus governance or entitlement logic with channel-local shortcuts.

---

## 5. Consumer and Channel Model

### 5.1. Telegram consumer requirements

A Telegram delivery target MUST be represented as governed consumer context with at least:

```text
consumer_id
consumer_type = telegram_channel or telegram_bot
active/suspended/blocked status
chat/channel target
delivery mode
allowed levels/themes if used
repeat_policy_id
schedule_id
entitlement/quota scope
owner or responsible operator
```

### 5.2. Demo consumer rule

Internal demo Telegram consumers MUST be clearly labeled as demo/internal and must not be confused with production-like public channels.

### 5.3. Channel rule

Telegram chat ID or target name alone is not enough. Delivery is governed by consumer record plus rules, not by bot token plus hardcoded channel.

---

## 6. Preflight and Real-Posting Gate

### 6.1. Minimum preflight checklist

Before enabling real Telegram posting, confirm:

```text
consumer exists and active
chat/channel target verified
worker credentials configured and protected
schedule configured
posting window configured if required
allowed content rules configured
repeat policy configured
entitlement/quota valid
worker uses API/selection engine
compatibility validation exists
delivery log exists
dry-run mode tested
failure handling and pause path documented
```

### 6.2. Real-posting gate

Real posting SHOULD not start until the following are proven:

```text
draft item cannot reach Telegram worker
incompatible item is blocked before send
send success is logged
send failure is logged
repeat window prevents duplicate delivery
quota or entitlement denial prevents posting
worker can operate in dry-run or simulated mode
```

### 6.3. Gate rule

“Bot can post one poll” is not sufficient proof of Telegram readiness.

---

## 7. Selection and Eligibility Path

### 7.1. Required request path

Telegram worker must request item selection through API/service contract that applies:

```text
consumer authorization
consumer status check
entitlement/quota check
status filtering
taxonomy/rule filtering
repeat policy
consumer compatibility filtering
reservation or idempotency handling where needed
```

### 7.2. Eligibility rule

Telegram worker MUST NOT post:

```text
draft
imported
normalized
needs_review
retired
blocked
```

### 7.3. No-eligible path

When no eligible item exists:

```text
record no-eligible outcome
record reason code if available
do not fall back to raw CSV or stale local cache
do not post substitute ungoverned content
surface coverage/rule issue to analytics or operations
```

---

## 8. Telegram Compatibility Validation

### 8.1. Validation inputs

Telegram compatibility validator SHOULD check:

```text
question text suitability
option count limits
option text suitability
correct answer representation
explanation availability/limits
poll/quiz mode requirements
consumer-specific send mode
supported item type
```

### 8.2. Projection rule

Telegram payload MUST be produced from canonical item version and consumer context. It MUST NOT parse raw source file or manually reconstructed text fragments.

### 8.3. Compatibility outcomes

Validation outcome SHOULD be one of:

```text
compatible
incompatible
compatible_with_truncation_or_transform_only_if_policy_allows
dry_run_only
```

### 8.4. Compatibility rule

If compatibility is uncertain, send must be blocked or downgraded to dry-run/simulated proof until explicit support exists.

---

## 9. Scheduling and Posting Window

### 9.1. Schedule contract

Telegram delivery SHOULD support or emulate:

```text
posting days
posting window start/end
timezone-aware execution
channel-local schedule context
missed-run handling
manual trigger path
```

### 9.2. Schedule rule

Worker must respect configured posting window and must not treat “job is running now” as permission to post outside channel policy.

### 9.3. Missed-run handling

If a scheduled run is missed:

```text
record missed or delayed run
apply documented catch-up or skip policy
avoid duplicate send caused by late rerun
```

---

## 10. Repeat Policy and Idempotency

### 10.1. Repeat rule

Each Telegram consumer MUST have repeat policy. Default expectation:

```text
same channel: avoid repeat within configured window
same consumer: avoid repeat until cycle exhausted or window expired
```

### 10.2. Reservation/idempotency rule

For scheduled or concurrent delivery, system SHOULD reserve selected item or otherwise apply idempotency protection before actual send to reduce duplicate-post races.

### 10.3. Duplicate-prevention path

Telegram worker SHOULD preserve:

```text
schedule run identifier
selection request identifier
idempotency key
delivery record identifier
telegram message identifier when available
```

### 10.4. Duplicate rule

Retry must never create uncontrolled duplicate posting. If delivery state is uncertain, system should prefer visible investigation over blind repeat send.

---

## 11. Send Execution and Delivery Logging

### 11.1. Send sequence

Expected send path:

```text
1. Scheduler or operator triggers run.
2. Worker loads Telegram consumer config.
3. Worker requests next eligible item.
4. Worker validates Telegram compatibility.
5. Worker sends payload or performs dry-run/simulation.
6. Worker records outcome and identifiers.
7. Analytics/operations can inspect result.
```

### 11.2. Delivery statuses

Delivery or payload status SHOULD distinguish:

```text
reserved
sent
failed
skipped
cancelled
dry_run
simulated
```

### 11.3. Minimum logged fields

Telegram delivery logs SHOULD preserve:

```text
delivery_id
consumer_id
quiz_item_id
quiz_item_version_id
channel type
target chat/channel identifier reference
schedule run or trigger reference
outcome status
reason code if not sent
telegram_message_id when available
created_at
```

### 11.4. Logging rule

If Telegram send happened but the platform cannot later show which item, which version, which channel and which outcome occurred, the Telegram path is operationally incomplete.

### 11.5. Current MVP worker path

The committed MVP worker path is:

```text
src/quizbank_mvp/telegram_delivery.py
tools/run_telegram_delivery_smoke.py
database/migrations/003_add_telegram_delivery_results.sql
```

The worker requests selection through `select_next_item`, creates the canonical
delivery id, builds a Telegram quiz-poll payload from the selected runtime item,
and records `sent`, `failed` or `skipped` in SQLite. Dry-run records `skipped`
with `dry_run_no_bot_api_call`; real send requires an explicit CLI approval flag
and a token supplied outside Git.

---

## 12. Failure Handling and Pause Paths

### 12.1. Send-failure handling

On Telegram send failure:

```text
record failure reason
do not mark delivery successful
apply retry only when idempotency is safe
avoid duplicate posts
surface repeated failures to operations
```

### 12.2. Incompatibility handling

On compatibility failure:

```text
block send
record validation reason
preserve candidate/item reference
route issue to content/admin/ops as needed
```

### 12.3. Pause/disable controls

Operations/admin MUST be able to:

```text
pause all Telegram delivery
pause one channel
disable one schedule
switch one consumer to dry-run
revoke worker credential path
block problematic item or source from Telegram through governed status/control path
```

### 12.4. Failure rule

Telegram incidents must degrade to “no post with explicit evidence”, not to silent failure and not to unsafe fallback content.

---

## 13. Dry-Run, Simulation and Demo Mode

### 13.1. Dry-run mode

Dry-run SHOULD:

```text
run selection and compatibility checks
build Telegram payload
not post to real channel
record dry-run artifact or log
```

### 13.2. Simulated delivery mode

Simulation MAY emulate Telegram posting for QA or demo proof when real posting is unsafe, unavailable or out of scope.

### 13.3. Demo-safe rule

Demo Telegram proof may be simulated, but it must be labeled as simulated/dry-run and must not be presented as real channel production behavior.

### 13.4. Negative controls

Telegram demo/pilot SHOULD be able to show at least one negative control such as:

```text
draft item blocked
incompatible item blocked
quota denied
consumer blocked
auth denied for unauthorized worker path
```

---

## 14. Security and Secret Handling

### 14.1. Security responsibilities

Telegram path must protect:

```text
worker credentials/tokens
authorized send path
hidden correct-answer handling
channel targeting integrity
delivery idempotency
auditability of operational overrides
```

### 14.2. Secret rule

Telegram token or equivalent credential MUST NOT appear in repository, screenshots, demo output or logs beyond approved secret-handling rules.

### 14.3. Answer-protection rule

Correct-answer metadata may flow inside the authorized worker-to-Telegram adapter path only as required by Telegram quiz mechanics. It must not leak through public API, learner-facing response or unauthorized logs.

---

## 15. Analytics, Metrics and Observability

### 15.1. Telegram metrics

Operations and analytics SHOULD track:

```text
scheduled runs
successful sends
failed sends
skipped/no-eligible runs
compatibility failures
repeat-policy blocks
quota or entitlement denials
dry-run/simulated deliveries
duplicate-post prevention events
```

### 15.2. Telegram evidence fields

Pilot/demo evidence SHOULD be able to show:

```text
channel or consumer identifier
selected quiz item/version
outcome status
message identifier or simulated artifact
reason for failure/skip when relevant
timestamp
```

### 15.3. Observability rule

Telegram delivery is not production-like unless failures, skips and denials are visible, not just successful sends.

---

## 16. QA and Verification Hooks

### 16.1. Telegram QA anchors

This playbook is expected to align with:

```text
QA-TG-001 .. QA-TG-010
SRS-TG-001 .. SRS-TG-012
UC-007
UC-021
UC-022
```

### 16.2. Minimum Telegram verification set

Verification SHOULD cover:

```text
worker does not read raw CSV
worker uses API/selection engine
draft item excluded
incompatible item blocked before send
successful send recorded
failed send recorded
retry/idempotency prevents duplicate posting
schedule respects consumer rules and entitlement
dry-run generates payload without posting
demo simulation remains clearly labeled
```

### 16.3. Launch implication

If Telegram path cannot prove governed selection, compatibility validation, logging and safe failure handling, pilot Telegram readiness is not achieved.

---

## 17. Anti-Patterns

The following are explicitly prohibited:

```text
Telegram bot with direct CSV access
hardcoded item selection in worker
posting draft or blocked item for convenience
retry loop that can create duplicate posts
real channel posting with no dry-run proof
manual Telegram posting presented as system automation without label
using Telegram as hidden core product logic
storing or exposing Telegram token in repo or demo materials
```

---

## 18. Acceptance Criteria

`18_telegram_delivery_playbook.md` is acceptable when:

1. It defines Telegram as governed consumer/adapter path, not source of truth.
2. It requires API/selection-engine-based delivery and forbids raw CSV selection.
3. It formalizes compatibility validation, schedule, repeat policy and idempotency handling.
4. It covers send logging, failure handling, pause paths, dry-run and simulation modes.
5. It includes security/secret rules and answer-leak prevention for Telegram flow.
6. It references Telegram QA/demo expectations and negative controls.
7. It defines a real-posting gate consistent with pilot readiness.

---

## 19. References

Primary references:

```text
CONSTITUTION.md
docs/02_requirements_srs.md
docs/03_use_cases.md
docs/04_domain_model.md
docs/08_security_threat_model.md
docs/09_quality_assurance.md
docs/10_operations.md
docs/13_stanford_presentation_outline.md
docs/17_admin_workflow.md
```

Key requirement anchors:

```text
SRS-TG-001..012
IF-TG-001..005
UC-007
UC-021
UC-022
QA-TG-001..010
SEC-GATE-DEMO-006
OPS Telegram operations sections
```

---

## 20. Final Telegram Rule

```text
Telegram delivery is acceptable only when it behaves as a controlled projection of
canonical platform logic: selected through governed rules, validated for channel
compatibility, logged for history, and observable under failure.
```
