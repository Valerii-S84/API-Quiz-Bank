# API Quiz Bank — Operations

**Документ:** `docs/10_operations.md`  
**Назва проєкту:** API Quiz Bank  
**Внутрішня історична назва:** QuizBank / German QuizBank Platform  
**Версія:** 1.0.0  
**Статус:** foundational operations plan, runbook standard and production-readiness contract; subordinate to `CONSTITUTION.md`; aligned with `00_vision.md`, `01_product_charter.md`, `02_requirements_srs.md`, `03_use_cases.md`, `04_domain_model.md`, `05_architecture.md`, `06_data_standard.md`, `07_api_standard.md`, `08_security_threat_model.md`, `09_quality_assurance.md`  
**Дата:** 2026-04-30  
**Мова:** українська з канонічними технічними термінами англійською  
**Власник:** project owner / authorized product maintainer  
**Операційний власник:** Operations Owner / Technical Lead  
**Керівні документи:** `CONSTITUTION.md`, `docs/00_vision.md`, `docs/01_product_charter.md`, `docs/02_requirements_srs.md`, `docs/03_use_cases.md`, `docs/04_domain_model.md`, `docs/05_architecture.md`, `docs/06_data_standard.md`, `docs/07_api_standard.md`, `docs/08_security_threat_model.md`, `docs/09_quality_assurance.md`  
**Наступні документи:** `11_billing_model.md`, `12_analytics_model.md`, `13_stanford_presentation_outline.md`, `14_roadmap.md`, `15_repository_governance.md`, `16_source_onboarding_playbook.md`, `17_admin_workflow.md`, `18_telegram_delivery_playbook.md`, `19_privacy_compliance.md`

---

## 0. Executive Summary

`10_operations.md` визначає, як **API Quiz Bank** має запускатися, підтримуватися, відновлюватися, моніторитися, оновлюватися і демонструватися як серйозна API-first educational content platform.

Цей документ не є декоративним “ops checklist”. Він є операційним контрактом, який переводить попередні документи в runbooks, gates, incident handling, backup/restore discipline, deployment rules, monitoring, support, rollback, production readiness and Stanford-style operational evidence.

Головна операційна теза:

```text
API Quiz Bank is not production-ready because the code runs.
API Quiz Bank is production-ready only when the platform can be operated, observed,
secured, recovered, changed, rolled back, explained and demonstrated with evidence.
```

Поточний operational baseline, який має підтримати операційна модель:

```text
115 active bank files
30,974 active rows/items
CEFR levels: A1, A2, B1, B2, C1, C2
18 themes
all active items currently in draft operational status
local constitution check: violations=0 for 30,974 rows
```

Цей baseline є стартовим активом. Операційна модель повинна підтримувати не тільки запуск поточного corpus, а й майбутнє розширення:

```text
New quiz files are onboarded, not dropped.
```

Тобто operations мають уміти безпечно виконувати:

```text
source intake
  → source_id
  → checksum
  → inventory
  → import_manifest.yml
  → parser assignment
  → dry-run import
  → canonical validation
  → duplicate/conflict classification
  → import batch
  → status workflow
  → approved/published delivery
  → generated reports
  → monitoring / audit / backup / launch evidence
```

Production claim для API Quiz Bank неможливий без:

```text
health/readiness checks
structured logs
metrics and dashboards
alerting or monitored operational signals
backup schedule
restore procedure
restore drill evidence
incident playbook
rollback/disable paths
migration discipline
release checklist
CI/CD or controlled deployment process
support/issue-reporting path
security operations
launch approval record
known limitations register
```

Operations must protect the central platform formula:

```text
source files
  → governed imports
  → canonical data
  → production database
  → selection engine
  → versioned API
  → Telegram / web / bots / schools / external clients
  → deliveries / attempts / analytics / billing / operations
```

Final operational rule:

```text
No public, paid, Stanford-demo or production claim may be made unless the system can show
what is running, what data it uses, what changed, what failed, what was delivered,
what was backed up, how it can be restored, how it can be rolled back,
and who is responsible for the next operational action.
```

---

## 1. Role of This Document

### 1.1. Purpose

`10_operations.md` defines the operational discipline for API Quiz Bank:

```text
environments
runtime ownership
health/readiness
monitoring
logging
metrics
alerts
backups
restore drills
incident response
maintenance mode
release process
deployment gates
rollback paths
migration operations
source/import operations
API operations
Telegram operations
billing/entitlement operations
security operations
support process
Stanford-style demo operations evidence
```

### 1.2. Place in the documentation hierarchy

```text
CONSTITUTION.md
  ↓
docs/00_vision.md
  ↓
docs/01_product_charter.md
  ↓
docs/02_requirements_srs.md
  ↓
docs/03_use_cases.md
  ↓
docs/04_domain_model.md
  ↓
docs/05_architecture.md
  ↓
docs/06_data_standard.md
  ↓
docs/07_api_standard.md
  ↓
docs/08_security_threat_model.md
  ↓
docs/09_quality_assurance.md
  ↓
docs/10_operations.md
  ↓
runbooks / deployment / monitoring / launch / support / production
```

If this document conflicts with `CONSTITUTION.md`, the Constitution wins. If this document conflicts with SRS P0 requirements, either this document must be corrected or a formal change-control decision must update SRS and affected traceability.

### 1.3. What this document does

This document:

- defines operational owners and responsibilities;
- defines environments and data policies;
- defines operational state model;
- defines health/readiness model;
- defines backup, restore and disaster recovery expectations;
- defines incident response model;
- defines release, rollback and migration rules;
- defines observability requirements;
- defines operations launch gates;
- defines support and issue-reporting baseline;
- defines Stanford-style operations evidence package;
- defines remaining documentation needed after this stage.

### 1.4. What this document does not do

This document is not:

- a cloud provider manual;
- a final Kubernetes/Terraform specification;
- a substitute for security threat model;
- a substitute for QA test plan;
- a billing provider guide;
- a privacy/legal policy;
- a full administrator UI manual;
- a repeated content audit of all quiz answers.

It defines **how the system must be operated**, regardless of the exact implementation stack chosen later.

---

## 2. Stanford-Style Operations Discipline

### 2.1. Meaning of Stanford-style in operations

For this project, Stanford-style operations means professional engineering evidence:

```text
clear operational goals
explicit owners
traceable requirements
repeatable runbooks
testable launch gates
monitored runtime behavior
controlled change management
backup and recovery evidence
incident handling
honest demo limitations
measurable reliability
```

It does not mean claiming association with Stanford. It means the project can survive serious technical review.

### 2.2. Operational traceability

Every critical operational capability must trace to:

```text
Vision objective
  → Product Charter gate
  → SRS requirement
  → Use case
  → Architecture component
  → QA test / operational drill
  → runbook
  → evidence artifact
```

Examples:

| Capability | Traceability path |
|---|---|
| Restore procedure | VOBJ-010 → AC-PROD-002 → UC-014 → QA-OPS-004 → restore runbook → restore_run report |
| Draft-blocking in delivery | VOBJ-006/VOBJ-008 → SRS-STAT/API/SEL → UC-005/UC-019 → QA-MVP-008 → production delivery monitor |
| New source onboarding | VOBJ-012 → SRS-ONB → UC-001/UC-002/UC-030 → QA-MVP-015 → source onboarding report |
| Telegram send failure | SRS-TG → UC-021 → QA-OPS-009 → Telegram worker dashboard |
| Quota denial | VOBJ-009 → SRS-BILL/API → UC-008 → QA-MVP-011 → quota_denials_total metric |

### 2.3. Evidence principle

Operational statements must be backed by evidence.

Bad:

```text
“We have backups.”
```

Good:

```text
“Backup job `backup_daily_prod_db` completed at 2026-04-30 02:00 UTC,
backup artifact `bkp_20260430_0200` passed checksum verification,
and restore drill `restore_20260430_staging` passed source/item/delivery/entitlement checks.”
```

### 2.4. Runbook quality rule

A runbook is acceptable only if a competent operator can execute it without guessing:

```text
trigger
owner
preconditions
commands or exact actions
expected outputs
verification steps
rollback/abort path
logs/evidence to keep
escalation path
post-action documentation
```

---

## 3. Operational Thesis

API Quiz Bank has two kinds of value:

```text
content value
platform trust
```

Operations protects platform trust.

The platform must be able to answer:

```text
What is running?
Which version is deployed?
Which data snapshot is active?
Which consumers are enabled?
Which sources are active?
Which items are approved/published?
Which items were delivered?
Which user/consumer attempted what?
Which entitlements allowed access?
Which failures happened?
Which backups exist?
Can we restore?
Can we rollback?
Who owns the incident?
What is safe to show in demo?
```

Operational failure can damage the product even if the content is correct. Therefore operations are part of product quality.

---

## 4. Operational Scope

### 4.1. In scope

Operations covers:

```text
repository operational discipline
environment lifecycle
configuration and secrets
runtime monitoring
health/readiness
logging and traces
metrics and dashboards
alerts
backup and restore
incident response
maintenance mode
release/deployment
migration operations
source/import operations
API operations
Telegram worker operations
billing/entitlement operations
analytics/reporting operations
security operations
support and issue management
Stanford demo reliability and fallback artifacts
```

### 4.2. Out of scope for this document

Out of scope:

- final cloud provider selection;
- exact infrastructure-as-code module definitions;
- detailed payment provider implementation;
- full privacy/legal terms;
- UI design for admin portal;
- AI/ML operations for future adaptive learning;
- full SOC 2/ISO compliance program;
- enterprise SSO operations.

### 4.3. MVP operations scope

MVP operations must include at least:

```text
local/demo environment
controlled data subset or current corpus snapshot report
basic health command or endpoint
structured logs for imports/API/delivery
source/import reports
manual or automated backup process for database/state
restore procedure draft
release checklist
rollback/disable notes
known limitations
Stanford demo operations checklist
```

### 4.4. Pilot operations scope

Closed pilot operations must include:

```text
staging or pilot environment
monitored API and worker processes
backup schedule
restore drill evidence
API/Telegram delivery logging
basic alerts or daily operational review
incident playbook
support channel
consumer disable path
source/item block path
quota/entitlement review path
```

### 4.5. Production operations scope

Production operations must include:

```text
production environment separation
managed or equivalent PostgreSQL backup strategy
restore drill evidence
monitoring dashboard
alert routing
incident severity model
release/rollback process
admin/security audit logs
secrets rotation procedure
support/abuse/issue-reporting path
launch approval and change log
```

---

## 5. Operational Inputs and Alignment

### 5.1. Core inputs

Operations must align with:

| Document | Operational input |
|---|---|
| `CONSTITUTION.md` | Binding platform rules, publication rules, API-first rule, source-of-truth rules |
| `00_vision.md` | Operations as product quality; launch discipline; operational trust metrics |
| `01_product_charter.md` | Product launch gates, operations gate, failure categories, rollback principle |
| `02_requirements_srs.md` | OPS/REL/ENG requirements, production acceptance criteria, demo requirements |
| `03_use_cases.md` | UC-014 restore backup, UC-015 Stanford demo, Telegram/API/import operations scenarios |
| `04_domain_model.md` | Operations entities: backup_artifact, restore_run, incident_record, operation_check |
| `05_architecture.md` | Observability architecture, backup/restore architecture, deployment architecture |
| `06_data_standard.md` | Data gates, generated reports, validation artifacts |
| `07_api_standard.md` | Health/readiness API, error model, idempotency, rate limits |
| `08_security_threat_model.md` | Operational threats, security logging, incident categories, security launch gates |
| `09_quality_assurance.md` | QA-OPS tests, CI gates, launch gate verification, demo evidence |

### 5.2. Platform facts to preserve

Operations must preserve these facts:

```text
raw files are source assets, not product delivery layer;
production database is operational source of truth after controlled import;
API is the external product surface;
selection engine is centralized;
Telegram is a consumer/worker, not the core product;
draft/imported/needs_review/blocked/retired items are not normal delivery-eligible;
new files must be onboarded;
deliveries must be logged;
entitlements and quotas must control access;
security and operations must be demonstrable.
```

### 5.3. Launch blocker alignment

Operations must treat the following as launch blockers for production:

```text
no backup;
no restore procedure;
no restore evidence;
no incident playbook;
no rollback path;
no monitoring/logging;
no known limitations register;
no owner assignment;
public consumers can access draft/blocked items;
Telegram worker reads raw CSV directly;
paid access bypasses entitlements;
secrets committed to repository;
critical admin actions are not logged;
```

---

## 6. Core Operations Principles

### Principle 1 — Operate before scaling

A system that cannot be observed, backed up, restored and rolled back is not ready to scale.

### Principle 2 — Evidence over optimism

Every readiness claim must have evidence: logs, reports, dashboards, test output, restore run, release checklist or demo artifact.

### Principle 3 — Disable paths are product safety

Operations must be able to disable:

```text
consumer
API key
affected endpoint
source file
import batch
quiz item
Telegram channel schedule
billing webhook handler
entitlement grant path
scheduler
worker
```

### Principle 4 — No invisible failures

A failed import, failed Telegram send, failed backup, failed billing webhook, quota drift or selection failure must be logged and visible.

### Principle 5 — Restore is more important than backup

Backup without tested restore is not operational readiness.

### Principle 6 — Demo is an environment, not a magic show

Stanford-style demo must have operational preparation, safe credentials, fallback artifacts and honest labels for implemented/simulated/planned functionality.

### Principle 7 — Source onboarding is operational work

Adding a new quiz file is not just content work. It is an operational event with source IDs, checksums, manifest changes, parser assignment, validation, reports and possible release impact.

### Principle 8 — Change control protects trust

Production-relevant changes must be traceable through commit, review, tests, release notes, migrations and launch gates.

### Principle 9 — Logs must help, not leak

Logs should support debugging, security investigation and audit. They must not leak raw tokens, secrets, unnecessary personal data or sensitive answer metadata outside allowed contexts.

### Principle 10 — Operations are part of the product narrative

The project must be able to show that it is not only built but governable, recoverable and supportable.

---

## 7. Operations Roles and Responsibilities

### 7.1. Role catalog

| Role | Responsibility |
|---|---|
| Project Owner | Final accountability for product direction, launch claims, risk acceptance |
| Product Maintainer | Maintains launch gates, roadmap, acceptance criteria, known limitations |
| Technical Lead | Architecture, runtime design, deployment strategy, migration discipline |
| Operations Owner | Monitoring, backups, restore, incident handling, runbooks, uptime readiness |
| Security Owner | Secrets, access controls, incident response for security events, audit readiness |
| Data/Content Lead | Source onboarding, import manifest, parser policy, data reports |
| QA Owner | Test evidence, release QA report, launch gate verification |
| Billing Owner | Entitlements, quotas, payment/webhook operations, customer access issues |
| Demo Owner | Demo environment, script, fallback artifacts, presentation claims |
| Support Owner | User/channel/API client reports, issue triage, support communications |

Small teams may combine roles, but responsibilities must remain distinct.

### 7.2. RACI matrix

| Operational decision/action | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| Production launch approval | Product Maintainer | Project Owner | Tech, QA, Security, Ops | All stakeholders |
| Backup policy | Operations Owner | Technical Lead | Security, Product | QA |
| Restore drill | Operations Owner | Technical Lead | QA, Data | Product |
| Incident severity assignment | Operations Owner | Project Owner for SEV-1 | Security, Tech, Product | Affected owners |
| API release | Technical Lead | Product Maintainer | QA, Security | Consumers if needed |
| Data migration | Technical Lead | Data/Content Lead | QA, Ops | Product |
| New source accepted | Data/Content Lead | Product Maintainer | QA, Tech | Ops |
| Telegram schedule change | Operations Owner | Product Maintainer | Telegram Owner, Billing | Support |
| Billing entitlement incident | Billing Owner | Product Maintainer | Security, Ops | Affected consumer |
| Secret rotation | Security Owner | Technical Lead | Ops | Product if risk impact |
| Demo readiness approval | Demo Owner | Project Owner | Product, Tech, QA, Ops | Demo participants |

### 7.3. Owner assignment rule

Every runbook must name an owner. Every incident must have a single incident owner. Every launch gate must have an approving owner.

---

## 8. Environment Model

### 8.1. Required environments

| Environment | Purpose | Data policy | External access |
|---|---|---|---|
| `local` | Development and unit tests | Fixtures or local subset | No public access |
| `ci` | Automated checks | Fixtures/generated data | No public access |
| `internal_dev` | Prototype integration | Controlled subset | Internal only |
| `staging` | Pre-release validation | Sanitized or controlled production-like data | Restricted |
| `demo` | Stanford-style demo | Safe demo data or labelled sanitized subset | Controlled demo access |
| `closed_pilot` | Limited real-world usage | Approved/published pilot subset | Selected consumers |
| `public_beta` | Broader external validation | Production-like controls | Public/beta users |
| `production` | Supported product | Full governed data | Public/paid/official consumers |

### 8.2. Environment promotion path

```text
local → ci → internal_dev → staging → demo/closed_pilot → public_beta → production
```

Promotion requires:

```text
schema validation passes;
migrations pass;
OpenAPI contract passes;
security smoke tests pass;
backup/restore path appropriate to environment exists;
known limitations are updated;
release checklist is signed;
```

### 8.3. Environment naming convention

Environment identifiers should be explicit:

```text
AQB_LOCAL
AQB_CI
AQB_DEV
AQB_STAGING
AQB_DEMO
AQB_PILOT
AQB_BETA
AQB_PROD
```

### 8.4. Environment isolation rules

```text
production secrets must not exist in local/demo;
demo credentials must not work in production;
CI must not use production database;
production logs/backups must be access-controlled;
demo data must be labelled;
staging may use sanitized/subset data unless approved;
public beta must not bypass security controls;
```

### 8.5. Demo environment rules

Demo environment must be:

```text
deterministic where possible;
free of secrets on screen;
able to show source onboarding;
able to call next quiz API;
able to show delivery logging;
able to demonstrate one negative control;
able to show generated reports;
able to fall back to screenshots/log snippets/report artifacts if live network fails;
```

---

## 9. Operational State Model

### 9.1. Platform operational states

| State | Meaning | Delivery allowed? |
|---|---|---|
| `initializing` | Service is starting | No |
| `healthy` | Service is operating normally | Yes |
| `degraded` | Some non-critical capability impaired | Limited, if safe |
| `maintenance` | Planned maintenance | No public delivery unless explicitly safe |
| `safe_mode` | Risk state; writes/delivery restricted | Usually no |
| `incident_active` | Incident declared | Depends on severity and controls |
| `read_only` | Reads allowed, writes disabled | Possibly API read-only; no delivery-producing requests |
| `delivery_paused` | Selection/API may work; scheduled delivery paused | API maybe; Telegram no |
| `import_paused` | Imports disabled | Existing delivery may continue if safe |
| `billing_paused` | Billing webhook/access changes paused | Delivery follows last known safe entitlements |
| `shutdown` | Service stopped | No |

### 9.2. State transition triggers

```text
planned deployment;
migration;
backup/restore;
incident;
security event;
source poisoning suspicion;
Telegram worker error spike;
billing webhook anomaly;
quota drift;
database error;
manual owner decision;
```

### 9.3. Safe mode rule

The system should enter or support safe mode when data integrity, security or delivery correctness is uncertain.

Safe mode should be able to:

```text
pause scheduled Telegram posts;
block delivery-producing next-quiz endpoint;
allow admin diagnosis;
allow health/readiness to report unsafe state;
prevent new imports;
prevent billing grant changes if webhook path is compromised;
show clear reason code;
```

---

## 10. Service and Component Catalog

### 10.1. Core services

| Component | Operational role | Criticality |
|---|---|---|
| API Service | Versioned API, consumer delivery, attempts, admin endpoints | Critical |
| PostgreSQL / Database | Operational source of truth | Critical |
| Selection Engine | Eligibility, anti-repeat, consumer-specific selection | Critical |
| Import Pipeline | Source parsing, normalization, validation, reports | Critical for data operations |
| Scheduler | Triggers Telegram/import/report jobs | Important |
| Telegram Worker | Posts/simulates scheduled quizzes | Important/Pilot critical |
| Billing Worker/Webhook Handler | Payment events → entitlements | Critical for paid launch |
| Analytics/Reports | Coverage, delivery, usage, operational reports | Important |
| Admin Workflow | Source/item/status/consumer operations | Critical for governance |
| Monitoring/Logging | Observability, incident analysis | Critical |
| Backup/Restore | Recovery from failure | Critical |

### 10.2. External dependencies

| Dependency | Use | Operational concern |
|---|---|---|
| Telegram Bot API | Telegram quiz/poll delivery | Send failures, token secrecy, idempotency |
| Payment provider | Payment signal source | Webhook verification, replay, provider outage |
| Git/GitHub or equivalent | Version control, PRs, CI | Required checks, branch protection |
| Hosting/cloud provider | Runtime infrastructure | Uptime, backups, network, secrets |
| Observability provider | Logs/metrics/alerts | Data retention, privacy, access |
| Email/support tool | User support | Incident/support communications |

### 10.3. Critical path map

```text
API delivery path:
consumer request
  → auth/authz
  → entitlement/quota
  → selection engine
  → production database
  → delivery/reservation log
  → response

Telegram path:
scheduler
  → Telegram worker
  → API/selection engine
  → Telegram compatibility validation
  → Telegram Bot API
  → delivery log
  → analytics

Source onboarding path:
file intake
  → source registry
  → checksum/inventory
  → manifest/parser
  → dry-run import
  → validation/duplicate report
  → canonical storage
  → status workflow
  → reports
```

---

## 11. Health and Readiness

### 11.1. Health check

Health check answers: “Is the process alive?”

Recommended endpoint or command:

```text
GET /health
```

Expected healthy response:

```json
{
  "status": "ok",
  "service": "api-quiz-bank-api",
  "environment": "staging",
  "version": "0.1.0",
  "timestamp": "2026-04-30T00:00:00Z"
}
```

Health must not perform expensive checks.

### 11.2. Readiness check

Readiness answers: “Can this service safely serve its role?”

Recommended endpoint or command:

```text
GET /readiness
```

Readiness should verify:

```text
database reachable;
database migrations current;
required configuration present;
critical secrets present without exposing them;
queue reachable if required;
cache reachable if required;
selection engine available;
no blocking maintenance/safe mode;
OpenAPI/version config present;
```

### 11.3. Worker readiness

Workers must expose or log readiness for:

```text
scheduler reachable;
queue subscription active;
Telegram token available and protected;
API/selection access available;
latest job heartbeat timestamp;
no stuck jobs above threshold;
```

### 11.4. Readiness must be honest

Readiness must fail if the system cannot safely perform delivery-producing operations.

Examples:

```text
database down → not ready;
migrations pending → not ready;
no entitlement config for paid API → not ready for paid delivery;
maintenance mode active → not ready for public delivery;
backup failure alone → may be degraded, but production launch gate fails until resolved;
```

### 11.5. Health/readiness evidence

Operations should keep examples of:

```text
healthy response;
not-ready response;
maintenance mode response;
dependency failure response;
```

for QA and demo readiness.

---

## 12. Reliability Model: SLIs, SLOs and Error Budgets

### 12.1. Reliability maturity note

MVP may not need formal contractual SLA. But it must define internal SLIs/SLOs for operational honesty. These targets can be revised after real usage data appears.

### 12.2. Core SLIs

| SLI | Definition | Phase |
|---|---|---|
| API availability | Fraction of successful health/readiness/API delivery checks | Pilot+ |
| Next-quiz success rate | Successful eligible quiz responses / next-quiz requests | MVP+ |
| Next-quiz latency | Time to return next eligible quiz response | Pilot+ |
| Delivery logging rate | Delivery-producing requests with delivery/reservation record | MVP+ |
| Draft-block violation count | Number of normal deliveries of draft/blocked items | MVP+; must be zero |
| Telegram send success rate | Successful sends / scheduled send attempts | Pilot+ |
| Import dry-run success rate | Successful dry-run imports / dry-run attempts | MVP+ |
| Backup success | Successful backup jobs within retention window | Pilot+ |
| Restore drill success | Successful restore drills / scheduled restore drills | Pilot/Production |
| Unauthorized access blocked | Auth/authz denials properly logged | MVP+ |
| Quota denial correctness | Quota denials match entitlement state | Pilot+ |

### 12.3. Suggested internal SLOs

Initial non-contractual internal targets:

| Phase | SLO |
|---|---|
| MVP | Demo API flow succeeds in controlled environment during rehearsal. |
| Closed pilot | Next-quiz endpoint p95 latency under 1000 ms for pilot dataset under expected load. |
| Closed pilot | No normal consumer receives draft/blocked item. Target: 0 violations. |
| Closed pilot | Telegram scheduled delivery failure visible within same operational review cycle. |
| Public beta | API uptime target defined and monitored. Initial target may be 99.0% unless infrastructure supports more. |
| Production | Production SLOs formally reviewed based on observed pilot/beta data. |

### 12.4. Error budget principle

Error budget logic should be used internally:

```text
If reliability or safety budget is exceeded, pause feature expansion and fix operations first.
```

Examples:

```text
repeated Telegram failures → pause channel scale;
quota denials wrong twice → pause paid expansion;
restore drill fails → no production launch;
draft delivery violation → immediate incident, pause delivery path;
```

### 12.5. Non-negotiable zero-tolerance events

Some failures are not allowed as “budgeted” errors:

```text
draft/blocked item delivered to normal consumer;
raw API key/token exposed;
consumer accesses another consumer’s private data;
paid access bypasses entitlements;
restore procedure falsely marks unhealthy data healthy;
Telegram worker reads raw CSV directly for production;
```

---

## 13. Observability Standard

### 13.1. Observability goal

Operations must make the system explainable during normal work and failure.

Minimum signals:

```text
metrics
structured logs
traces/correlation IDs where feasible
audit events
reports
dashboards
alerts or monitored review tasks
```

### 13.2. Correlation IDs

Every API request should have:

```text
request_id
trace_id if available
consumer_id where applicable
actor_id where applicable
operation
endpoint or job name
reason_code
outcome
```

Worker jobs should have:

```text
job_id
correlation_id
consumer_id/channel_id where applicable
source_id/import_batch_id where applicable
attempt number
idempotency key where applicable
outcome
```

### 13.3. Observability scope by component

| Component | Required visibility |
|---|---|
| API | requests, latency, errors, auth failures, quota denials, next-quiz outcomes |
| Selection engine | candidate counts, exclusion reasons, no-eligible reasons, repeat blocks |
| Import pipeline | source_id, batch_id, validation failures, duplicates, dry-run result |
| Telegram worker | scheduled jobs, sends, failures, retries, Telegram message IDs |
| Billing webhook | event accepted/rejected, signature failures, entitlement updates, idempotency |
| Admin actions | source registration, parser assignment, status changes, overrides |
| Database | migration state, connection health, slow queries if available, backup status |
| Analytics | report generation status, data freshness, generation failures |

---

## 14. Metrics Catalog

### 14.1. API metrics

```text
api_requests_total{endpoint,method,status_code,consumer_type}
api_request_duration_ms{endpoint,method}
api_errors_total{endpoint,reason_code}
api_auth_failures_total{reason_code}
api_authorization_denials_total{object_type,reason_code}
api_rate_limit_hits_total{consumer_id_or_type}
api_problem_details_total{type,status}
```

### 14.2. Quiz delivery metrics

```text
quiz_next_requests_total{consumer_type}
quiz_next_success_total{consumer_type,level,theme}
quiz_next_no_eligible_total{consumer_type,reason_code}
quiz_next_quota_denied_total{consumer_type,plan}
delivery_records_created_total{channel,status}
delivery_failures_total{channel,reason_code}
repeat_policy_blocks_total{consumer_type}
draft_delivery_violations_total
```

`draft_delivery_violations_total` must be zero. Any non-zero value is incident-level.

### 14.3. Selection metrics

```text
selection_requests_total{consumer_type}
selection_candidate_count{level,theme}
selection_filtered_by_status_total{status}
selection_filtered_by_repeat_total
selection_filtered_by_entitlement_total
selection_filtered_by_compatibility_total
selection_duration_ms
```

### 14.4. Source/import metrics

```text
source_files_registered_total{state}
source_checksum_duplicates_total
import_runs_total{mode,status}
import_rows_seen_total{source_id}
import_candidates_created_total{source_id}
import_validation_failures_total{rule_id,severity}
import_duplicate_candidates_total{case_type}
import_dry_run_duration_ms{source_id}
canonical_validation_pass_rate
```

### 14.5. Telegram metrics

```text
telegram_scheduled_jobs_total{channel_id,status}
telegram_send_success_total{channel_id}
telegram_send_failures_total{channel_id,reason_code}
telegram_retry_attempts_total{channel_id}
telegram_payload_validation_failures_total{rule_id}
telegram_duplicate_prevented_total{channel_id}
telegram_worker_heartbeat_timestamp
```

### 14.6. Billing/entitlement metrics

```text
billing_webhook_events_total{provider,event_type,outcome}
billing_webhook_signature_failures_total{provider}
billing_webhook_replay_blocked_total{provider}
entitlement_grants_total{plan,feature}
entitlement_revocations_total{reason_code}
quota_usage_total{consumer_id_or_type,quota_type}
quota_denials_total{reason_code}
manual_entitlement_overrides_total{actor_role,reason_code}
```

### 14.7. Operations metrics

```text
backup_success_timestamp{environment}
backup_failures_total{environment,reason_code}
backup_size_bytes{environment}
restore_drills_total{environment,status}
restore_duration_ms{environment}
incidents_total{severity,category}
incident_time_to_detect_ms{severity}
incident_time_to_recover_ms{severity}
release_deployments_total{environment,outcome}
rollback_events_total{environment,reason_code}
maintenance_mode_active{environment}
```

### 14.8. Security metrics

```text
secrets_scan_failures_total
unauthorized_requests_total{endpoint,reason_code}
object_authorization_denials_total{object_type}
admin_high_risk_actions_total{action_type}
api_key_created_total
api_key_revoked_total
secret_rotation_events_total{secret_type}
```

### 14.9. Analytics/reporting metrics

```text
reports_generated_total{report_type,status}
report_generation_duration_ms{report_type}
coverage_report_freshness_seconds
analytics_data_lag_seconds
delivery_analytics_records_total
attempt_analytics_records_total
```

---

## 15. Logging Standard

### 15.1. Log format

Logs should be structured JSON or equivalent structured format.

Minimum fields:

```text
timestamp
service
environment
version
operation
request_id or job_id
actor_id where applicable
consumer_id where applicable
source_id where applicable
quiz_item_id where applicable
import_batch_id where applicable
status/outcome
reason_code
message
```

### 15.2. Log levels

| Level | Use |
|---|---|
| `debug` | Local diagnosis only, disabled or limited in production |
| `info` | Normal important events: job complete, delivery success, import report generated |
| `warn` | Suspicious or degraded state: no eligible item, retry, quota near limit |
| `error` | Failed operation requiring review: send failure, import failure, webhook rejection |
| `critical` | Data exposure, draft delivery violation, backup failure with no recent valid backup, security incident |

### 15.3. Log redaction rules

Logs MUST NOT contain:

```text
raw API keys
auth tokens
Telegram bot token
payment provider secrets
webhook signing secrets
DB passwords
full payment data
private learner data unless explicitly necessary and protected
raw source content beyond controlled debug context
correct answer keys in public/learner-facing logs
```

### 15.4. Audit log vs operational log

Operational logs can rotate and summarize. Audit logs for critical actions must be durable.

Critical audit events:

```text
admin login/logout where applicable;
API key creation/revocation;
source registration;
parser assignment;
manifest change;
dry-run import;
import commit;
status approve/publish/retire/block;
manual entitlement override;
billing webhook accepted/rejected;
consumer disable/enable;
secret rotation;
backup/restore action;
incident opened/closed;
launch approval;
```

### 15.5. Log retention

Initial recommended retention:

| Log type | MVP/Pilot | Production target |
|---|---:|---:|
| Operational app logs | 14–30 days | 30–90 days |
| Security/audit logs | 90 days | 180–365 days, depending on privacy/legal posture |
| Demo logs | Until demo review complete | Archive only safe evidence |
| Import reports | Indefinite or tied to source history | Indefinite for production-relevant imports |
| Backup/restore logs | At least backup retention period | 1 year recommended for production evidence |

Retention must respect privacy/legal requirements.

---

## 16. Alerting and Operational Review

### 16.1. Alert philosophy

Alerts should notify humans only when action is required. Dashboards and daily reviews can handle non-urgent signals.

### 16.2. Must-alert events

Immediate alert or owner notification for:

```text
draft_delivery_violations_total > 0;
production API unavailable or readiness false for sustained window;
database unavailable;
backup failure when no recent valid backup exists;
restore drill failure during production readiness;
security authz anomaly spike;
Telegram token suspected leaked;
payment webhook signature failures spike;
entitlement grants behaving incorrectly;
large unexpected quota drift;
source/import poisoning suspicion;
critical secrets found in repository;
```

### 16.3. Should-alert events

```text
API error rate above threshold;
next-quiz latency above threshold;
Telegram send failures above threshold;
no-eligible item spike;
import failures;
coverage report generation failure;
worker heartbeat missing;
rate-limit spikes;
manual override spike;
```

### 16.4. Daily/weekly operational review

For MVP/Pilot, if real-time alerting is not mature, an operational review must check:

```text
API health
worker heartbeats
last backup success
delivery failures
Telegram failures
quota denials
unauthorized attempts
import/report failures
open incidents
known limitations
```

### 16.5. Alert record format

```text
alert_id
alert_name
severity
trigger_time
detected_by
metric/log/source
affected_component
affected_consumers
initial_owner
current_status
actions_taken
resolved_at
linked_incident_id
```

---

## 17. Dashboards

### 17.1. MVP dashboard

MVP dashboard or generated report should show:

```text
corpus status counts
items by CEFR/theme
approved/published count
source inventory status
latest import reports
API next-quiz successes/failures
delivery log count
quota denial demo count
last backup timestamp if backup exists
known limitations
```

### 17.2. Pilot dashboard

Pilot dashboard should show:

```text
API latency and error rate
next-quiz success/no-eligible/quota-denied
Telegram delivery success/failure
consumer delivery counts
repeat-policy blocks
import job status
backup status
security denials
incident status
```

### 17.3. Production dashboard

Production dashboard should show:

```text
availability/readiness
latency percentiles
error rates by reason code
security anomalies
backup freshness
worker health
billing webhook health
quota usage
consumer status
incident timeline
release version
```

### 17.4. Stanford demo dashboard

Demo dashboard should show:

```text
corpus baseline
source onboarding evidence
canonical validation evidence
API next-quiz evidence
delivery log evidence
negative control evidence
Telegram simulated/real delivery evidence
operations readiness summary
```

---

## 18. Backup Policy

### 18.1. Backup goal

Backups protect the ability to recover source governance, canonical data, delivery history, entitlements, audit records and operational evidence.

### 18.2. Backup scope

Must back up:

```text
PostgreSQL database;
source registry metadata;
import manifests;
file inventory;
parser profiles;
canonical quiz items and versions;
quiz options;
taxonomy files/records;
consumer records and rules;
delivery records;
attempt records where applicable;
entitlements and quota usage;
audit logs where stored in DB;
import reports;
generated operational reports;
OpenAPI/data schemas;
repository release artifacts;
```

Must preserve separately or with controlled storage:

```text
raw source files;
object storage metadata;
source checksums;
configuration excluding secrets;
```

Secrets should not be backed up casually with application data unless using a secure secret-management backup process.

### 18.3. Backup schedule

| Environment | Minimum backup policy |
|---|---|
| local | Not required; developer responsibility |
| CI | Not required; ephemeral fixtures |
| demo | Backup before major demo if stateful demo data matters |
| staging | Backup before risky migration/import |
| closed_pilot | Daily backup or backup before/after operational changes |
| public_beta | Automated daily backup; retention defined |
| production | Automated daily backup plus point-in-time recovery where feasible |

### 18.4. Backup before risky operations

Create or verify recent backup before:

```text
production migration;
large import commit;
batch status publication;
billing entitlement migration;
major release;
source manifest restructuring;
manual data correction;
public demo using production-like data;
```

### 18.5. Backup artifact metadata

Each backup artifact should record:

```text
backup_id
environment
database_name/source
started_at
completed_at
status
backup_type              -- full, incremental, logical dump, snapshot, PITR base, etc.
size_bytes
checksum/hash
retention_until
created_by/job_name
schema_version
application_version
included_components
storage_location_reference
restore_tested_status
notes
```

### 18.6. Backup retention

Initial suggested retention:

| Phase | Retention |
|---|---|
| MVP/demo | Keep at least latest known-good backup and demo artifacts |
| Closed pilot | 7–14 daily backups, plus pre-release backups |
| Public beta | 14–30 days, adjusted by cost/privacy |
| Production | 30+ days or policy-defined; longer for audit/import reports |

### 18.7. Backup integrity checks

Backup job must verify:

```text
backup completed successfully;
artifact exists;
artifact size is non-zero and plausible;
checksum recorded;
metadata recorded;
alert/log generated;
```

Full confidence requires restore drill.

---

## 19. Restore and Disaster Recovery

### 19.1. Restore goal

Restore must prove that the platform can recover not only database rows, but operational truth:

```text
sources
imports
canonical items
options
statuses
consumers
rules
entitlements
quotas
deliveries
attempts
audit logs
reports
```

### 19.2. Restore types

| Restore type | Purpose |
|---|---|
| Full environment restore | Rebuild complete environment from backup |
| Database restore | Restore PostgreSQL state |
| Point-in-time recovery | Restore to specific time before incident/corruption |
| Partial restore | Restore limited data if policy allows |
| Restore drill | Test restore in non-production environment |
| Migration rollback restore | Restore before/after failed schema migration |
| Demo fallback restore | Restore demo environment before presentation |

### 19.3. Restore runbook

Minimum restore flow:

```text
1. Declare restore action or drill.
2. Assign restore owner.
3. Identify environment and target restore point.
4. Enter maintenance/safe mode if production risk exists.
5. Select backup artifact.
6. Validate artifact metadata and checksum.
7. Restore to isolated target first when feasible.
8. Apply or verify migrations as needed.
9. Run health/readiness checks.
10. Run data consistency verification.
11. Run selection/API smoke tests.
12. Verify delivery history and entitlements.
13. Record restore_run evidence.
14. Decide whether to promote restored state or continue investigation.
15. Exit maintenance mode only after verification passes.
```

### 19.4. Restore verification checklist

After restore, verify:

```text
source_files count and checksums;
import_manifest entries;
import_batches and reports;
quiz_items and quiz_item_versions;
quiz_options and correct answer references;
status history;
taxonomy records;
consumer records;
consumer rules;
entitlements and quota usage;
delivery records;
attempt records if applicable;
audit logs;
latest generated reports;
API readiness;
next-quiz endpoint on safe demo consumer;
draft/blocked item exclusion;
quota denial behavior;
```

### 19.5. Restore failure rule

If restore verification fails:

```text
do not mark system healthy;
do not resume production delivery;
open or update incident;
escalate to Operations Owner and Technical Lead;
record failed restore evidence;
choose next restore point or rollback plan;
```

### 19.6. RPO/RTO targets

Initial targets should be honest and revisable.

| Phase | RPO target | RTO target | Notes |
|---|---:|---:|---|
| MVP/demo | Best effort / before demo backup | Same day | Acceptable if limitations documented |
| Closed pilot | 24 hours | Same business day | Real pilot data requires backup discipline |
| Public beta | 24 hours or better | 4–8 hours target | Depends on hosting maturity |
| Production | Defined by business plan | Defined by support/SLO policy | Must be reviewed before paid scale |

### 19.7. Disaster recovery triggers

```text
database corruption;
failed migration;
large accidental deletion;
source/import poisoning;
security compromise requiring rollback;
major hosting outage;
billing entitlement corruption;
Telegram worker duplicate flood;
```

### 19.8. Disaster recovery principle

No production launch without:

```text
documented restore procedure;
recent backup evidence;
at least one successful restore drill or controlled equivalent;
restore verification checklist;
owner assignment;
```

---

## 20. Database Operations

### 20.1. Database role

After controlled import, the production database is the operational source of truth for:

```text
sources/imports metadata;
canonical quiz items;
status lifecycle;
consumers/rules;
deliveries/attempts;
entitlements/quotas;
audit logs;
reports metadata;
```

### 20.2. Database operational requirements

```text
migrations are versioned;
indexes exist for critical selection/API queries;
manual DB edits are prohibited unless logged as emergency change;
pre-migration backup or backup validation required for risky changes;
failed migration has rollback or restore path;
```

### 20.3. Migration checklist

Before migration:

```text
migration reviewed;
schema impact documented;
backup exists or backup freshness verified;
CI migration tests pass;
data migration sample tested;
rollback/restore plan exists;
maintenance window considered;
```

During migration:

```text
record start time;
run migration command;
capture output;
monitor errors;
prevent concurrent unsafe writes if needed;
```

After migration:

```text
run readiness check;
run data consistency smoke checks;
run API next-quiz smoke test;
run draft-blocking test;
record migration result;
update release notes;
```

### 20.4. Database consistency checks

Minimum checks:

```text
quiz item has current version;
quiz item has options;
correct_option_ids reference existing options;
approved/published items have CEFR/theme;
all production items have source_id;
all production items have content_hash;
delivery records reference existing consumer and item;
entitlements reference existing consumer/customer;
no delivery record references blocked status at time of delivery unless incident/demo override documented;
```

### 20.5. Database anti-patterns

Forbidden:

```text
schema changes without migrations;
manual production edits without audit;
deleting delivered items and breaking history;
publishing items by direct DB update with no status event;
changing entitlement records manually without reason/audit;
restoring backup without verification;
```

---

## 21. Source and Import Operations

### 21.1. Import operations principle

Import is a controlled operational workflow, not a script someone runs casually.

### 21.2. Import modes

| Mode | Writes production items? | Use |
|---|---:|---|
| `dry_run` | No | Parse/validate/report before commit |
| `canonical_write` | Staging/canonical layer | Create normalized/canonical records without publication |
| `production_write` | Yes, controlled | Commit approved flow according to workflow |
| `reimport` | Controlled | Repeat import with version/change handling |
| `rollback_import` | Controlled | Undo or supersede import batch if supported |

### 21.3. Import run requirements

Every import run must record:

```text
import_batch_id
source_id
source checksum
manifest version
parser profile version
actor/job
mode
start/end time
rows seen
candidates created
validation failures
duplicate/conflict counts
items created/updated
status
report path
```

### 21.4. Dry-run gate

Dry-run must happen before committing a new or materially changed source.

Dry-run report must include:

```text
accepted rows;
skipped rows;
validation errors;
unknown taxonomy values;
invalid answer references;
duplicate candidates;
conflict candidates;
Telegram compatibility issues;
source traceability summary;
recommendation: proceed / fix / reject;
```

### 21.5. Import failure handling

If import fails:

```text
mark import_batch failed;
record reason_code;
prevent partial production corruption;
quarantine partial candidates if needed;
notify Data/Content Lead;
create issue if repeatable;
do not hide failure under successful report;
```

### 21.6. Production import gate

Before production import effect:

```text
source_id exists;
checksum recorded;
manifest entry exists;
parser profile assigned;
dry-run report exists;
validation report acceptable;
duplicates/conflicts classified;
status workflow defined;
backup or rollback path exists for large import;
release note drafted if corpus changes;
```

### 21.7. Reimport policy

Reimport must not silently replace production content. It must decide:

```text
same item no change;
new version;
metadata update;
new variant;
retire old item and replace;
reject conflicting item;
manual review required;
```

---

## 22. Future Source Onboarding Operations

### 22.1. Onboarding principle

```text
New quiz files are onboarded, not dropped.
```

### 22.2. Source onboarding states

```text
candidate
registered
parser_pending
parser_assigned
dry_run_failed
dry_run_passed
imported
active
archived
rejected
blocked
```

### 22.3. Onboarding runbook

```text
1. Receive proposed source file.
2. Create source intake record.
3. Assign stable source_id.
4. Compute checksum.
5. Add inventory record.
6. Classify format/encoding/expected item count.
7. Add import_manifest entry.
8. Assign parser profile or mark parser_pending.
9. Run dry-run import.
10. Generate onboarding/import report.
11. Validate canonical schema.
12. Classify duplicates/conflicts.
13. Resolve or route issues.
14. Import accepted candidates into controlled storage.
15. Move items through status workflow.
16. Publish only approved/published items.
17. Update generated inventory/coverage reports.
18. Record release note if production corpus changed.
```

### 22.4. Onboarding evidence package

Each future source onboarding must produce:

```text
source intake record;
source_id;
checksum;
file_inventory entry;
import_manifest entry;
parser_profile reference;
dry-run report;
validation report;
duplicate/conflict report;
import_batch record;
status summary;
coverage delta report;
release note if production-relevant;
```

### 22.5. Source blocking path

Operations must allow blocking a source when:

```text
source checksum mismatch;
format/parser mismatch;
rights/ownership unclear;
high validation failure rate;
answer conflict detected;
security/source poisoning suspicion;
```

When blocked:

```text
no new items from source may be delivered;
existing items from source may be blocked if risk affects them;
incident or issue record must explain reason;
```

---

## 23. API Operations

### 23.1. API operational responsibilities

API operations must protect:

```text
versioned route behavior;
authentication;
object-level authorization;
entitlement/quota enforcement;
status filtering;
public-safe projections;
Problem Details errors;
delivery logging;
rate limiting/usage controls;
health/readiness;
```

### 23.2. API release checklist

Before API release:

```text
OpenAPI contract updated if routes/schemas changed;
contract tests pass;
auth/authz tests pass;
Problem Details schemas pass;
rate limits or usage controls unchanged or documented;
backward compatibility impact assessed;
consumer impact documented;
release notes updated;
rollback path exists;
```

### 23.3. API smoke tests

Minimum smoke tests after deployment:

```text
GET /health returns ok;
GET /readiness returns ready;
GET /v1/taxonomy/themes or equivalent works;
POST /v1/quiz-items/next for demo consumer returns approved/published item;
normal consumer cannot receive draft/blocked item;
quota-denied scenario returns machine-readable error;
unauthorized request denied;
learner-safe projection does not expose hidden correct answers;
delivery/reservation record created for delivery-producing request;
```

### 23.4. API degradation modes

Allowed degradation options:

```text
read-only mode;
admin-only mode;
new delivery paused;
consumer-specific disable;
rate-limit tightening;
feature flag disable;
maintenance response;
```

### 23.5. API incident examples

```text
API down;
readiness false;
latency spike;
wrong status filtering;
entitlement check bypass;
BOLA/security issue;
quota drift;
Problem Details schema mismatch;
OpenAPI contract not matching implementation;
```

---

## 24. Selection Engine Operations

### 24.1. Selection operational goal

Selection must be explainable and safe.

For a selected item, system should be able to explain:

```text
consumer_id;
consumer rules;
entitlement/quota state;
requested filters;
eligible status;
level/theme/objective/pattern;
repeat policy result;
exclusion counts;
selected item_id;
delivery/reservation id;
reason codes;
```

### 24.2. Selection debug record

Recommended selection debug fields:

```text
selection_request_id
consumer_id
requested_level/theme/objective/pattern
allowed_levels/themes
candidate_count_initial
excluded_by_status
excluded_by_entitlement
excluded_by_quota
excluded_by_repeat
excluded_by_compatibility
candidate_count_final
selected_item_id
no_eligible_reason if none
created_delivery_or_reservation_id
latency_ms
```

### 24.3. Selection safety checks

Selection must never return:

```text
draft item;
imported item;
normalized item;
needs_review item;
retired item;
blocked item;
item outside consumer entitlement;
item violating repeat policy unless explicit override;
item incompatible with target consumer;
```

### 24.4. No-eligible operational path

When no eligible item exists:

```text
return machine-readable reason;
do not bypass status rules;
do not fall back to raw CSV;
do not select draft content;
record no-eligible metric;
use analytics to identify coverage gap;
```

---

## 25. Telegram Operations

### 25.1. Telegram operational principle

Telegram is a delivery consumer/worker. It is not the source of truth, not the selector, not the billing controller and not the content governance layer.

### 25.2. Telegram worker responsibilities

```text
load active Telegram consumer config;
respect schedule and posting window;
request quiz via API/selection engine;
validate Telegram compatibility;
send poll/quiz;
record Telegram message ID;
record success/failure;
respect idempotency/retry policy;
never read raw CSV for production;
```

### 25.3. Telegram preflight checklist

Before real channel posting:

```text
consumer exists and active;
channel/chat ID verified;
bot has required permissions;
schedule configured;
allowed levels/themes configured;
entitlement/quota valid;
repeat policy configured;
Telegram token protected;
worker uses API/selection engine;
payload compatibility validation exists;
dry-run payload tested;
delivery log enabled;
failure handling enabled;
```

### 25.4. Telegram send failure handling

On failure:

```text
record failure reason;
do not mark delivery successful;
apply retry policy only if idempotency is safe;
avoid duplicate posts;
alert if failures exceed threshold;
pause channel if repeated failures;
notify Telegram Channel Owner if required;
```

### 25.5. Telegram pause/disable paths

Operations must support:

```text
pause all Telegram delivery;
pause one channel;
disable one schedule;
revoke Telegram worker token;
switch channel to dry-run mode;
block a problematic item from Telegram only if consumer compatibility issue;
```

### 25.6. Telegram incident examples

```text
failed sends;
duplicate posts;
wrong channel;
draft item posted;
quota ignored;
bot token leaked;
Telegram API unavailable;
message ID not recorded;
```

---

## 26. Billing and Entitlement Operations

### 26.1. Billing operations principle

Payment provider events are signals. Internal entitlements are access truth.

### 26.2. Operational responsibilities

Billing operations must ensure:

```text
plans exist;
entitlements exist;
quota model exists;
usage is recorded;
manual overrides are audited;
webhook signatures are verified;
webhook events are idempotent;
cancellations/revocations are applied;
entitlement drift is detectable;
paid access can be disabled safely;
```

### 26.3. Billing webhook runbook

For each webhook event:

```text
1. Receive event.
2. Verify signature.
3. Check event idempotency/replay status.
4. Map external customer/subscription to internal customer/consumer.
5. Apply entitlement grant/revoke/update.
6. Record billing_event.
7. Record entitlement event.
8. Return provider-appropriate response.
9. Monitor failures/retries.
```

### 26.4. Manual entitlement override

Manual overrides require:

```text
actor;
consumer/customer;
feature/plan/quota;
reason;
valid_until;
approval if high-impact;
audit log;
review date;
```

### 26.5. Billing incident examples

```text
fake webhook accepted;
valid webhook rejected repeatedly;
subscription cancellation not reflected;
quota not decremented;
consumer receives premium content without entitlement;
manual override forgotten;
provider outage;
```

---

## 27. Admin Operations

### 27.1. Admin actions considered high-risk

```text
source registration;
source blocking/unblocking;
parser assignment;
manifest changes;
import commit;
batch approval;
quiz item publish/retire/block;
consumer enable/disable;
quota override;
entitlement override;
API key creation/revocation;
secret rotation;
manual database correction;
launch approval;
```

### 27.2. Admin audit requirements

Every high-risk admin action must record:

```text
action_id
actor_id
action_type
subject_type
subject_id
previous_state
new_state
reason_code
reason_note if needed
timestamp
request_id/job_id
```

### 27.3. Admin emergency change rule

Emergency changes may happen only when:

```text
risk is immediate;
owner approves or is unavailable under incident policy;
action is logged;
rollback path is defined;
post-incident review records why normal change process was bypassed;
```

---

## 28. Analytics and Reporting Operations

### 28.1. Analytics operations principle

Analytics must be derived from system records, not invented for presentation.

### 28.2. Required generated reports

```text
corpus snapshot report;
file inventory report;
import report;
coverage report;
status distribution report;
delivery report;
quota usage report;
security/audit event summary;
operations readiness report;
release QA report;
```

### 28.3. Report metadata

Every generated report should include:

```text
report_id
report_type
generated_at
environment
data_snapshot_time
source query/version
input artifacts
status
limitations
```

### 28.4. Report freshness

| Report | MVP/Pilot freshness | Production target |
|---|---|---|
| Corpus snapshot | On demand / before demo | Scheduled or on release |
| Coverage report | On import/release | Daily or on corpus change |
| Delivery report | On demand | Near real-time or daily |
| Quota usage | On demand | Near real-time for paid access |
| Operations readiness | Before launch/demo | Each release candidate |

---

## 29. Security Operations

### 29.1. Security operations responsibilities

Security operations must cover:

```text
secret management;
API key lifecycle;
admin authentication;
object-level authorization monitoring;
rate limiting/abuse control;
webhook verification;
security audit logs;
incident detection;
secret rotation;
dependency/security scanning;
security launch gates;
```

### 29.2. Secrets management

Secrets must not be committed to repository.

Secrets include:

```text
API keys;
JWT signing secrets;
Telegram bot token;
payment provider secret keys;
webhook signing secrets;
DB credentials;
cloud credentials;
observability provider credentials;
```

### 29.3. Secret rotation triggers

Rotate secrets when:

```text
suspected leak;
team member access changes;
provider requires rotation;
incident response requires it;
production launch from demo/prototype;
regular rotation interval reached;
```

### 29.4. API key lifecycle

API keys should support:

```text
creation;
scoped permission;
hash/protected storage;
last-used tracking where feasible;
revocation;
rotation;
owner association;
usage limits;
```

### 29.5. Security monitoring events

Must monitor/log:

```text
authentication failures;
object-level authorization denials;
rate limit triggers;
webhook signature failures;
admin high-risk actions;
secret rotation;
API key creation/revocation;
consumer access anomalies;
logs with suspected secret leakage;
```

### 29.6. Security incident escalation

Escalate immediately for:

```text
secret/token leak;
unauthorized consumer data access;
raw answer/correct-answer leak beyond allowed context;
admin account compromise;
payment webhook compromise;
draft/blocked content delivery caused by access-control failure;
```

---

## 30. Incident Response

### 30.1. Incident definition

An incident is any unplanned event that can affect:

```text
content delivery correctness;
API availability;
data integrity;
security/privacy;
billing/entitlement correctness;
Telegram channel trust;
backup/recovery capability;
external demo credibility;
```

### 30.2. Incident lifecycle

```text
detect
  → classify severity
  → assign owner
  → contain
  → diagnose
  → mitigate
  → recover
  → verify
  → communicate
  → close
  → post-incident review
  → follow-up actions
```

### 30.3. Incident record fields

```text
incident_id
severity
category
summary
started_at
detected_at
owner
affected_components
affected_consumers
affected_data
customer/user impact
initial hypothesis
actions_taken
current_status
resolved_at
root_cause_summary
follow_up_tasks
post_incident_review_link
```

### 30.4. Incident categories

| Category | Examples |
|---|---|
| API availability | API down, readiness false, latency severe |
| Data integrity | failed migration, corrupted import, wrong status state |
| Content delivery safety | draft item delivered, wrong consumer rules, repeat violation |
| Security | API key leak, BOLA, admin compromise, auth bypass |
| Billing/entitlement | paid access bypass, quota drift, webhook failure |
| Telegram | failed scheduled send, duplicate send, wrong channel |
| Source/import | source poisoning, parser failure, duplicate conflict ignored |
| Operations | backup failure, restore failure, monitoring down |
| Demo | live demo failure, wrong claim, unsafe data displayed |

### 30.5. First response checklist

```text
1. Confirm signal.
2. Open incident record.
3. Assign severity and owner.
4. Identify affected component/consumer/data.
5. Contain: pause delivery, disable endpoint, block source/item/consumer, revoke key if needed.
6. Preserve logs/evidence.
7. Communicate internally.
8. Fix or rollback.
9. Verify recovery.
10. Document timeline and follow-up.
```

---

## 31. Incident Severity Model

### 31.1. Severity levels

| Severity | Meaning | Examples | Response expectation |
|---|---|---|---|
| SEV-1 | Critical trust/safety/production impact | data exposure, public API down for paid users, draft item delivered broadly, secret leak | Immediate containment and owner escalation |
| SEV-2 | Significant product impact | Telegram delivery broken, quota wrong, webhook broken, restore failure during launch | Same-day response for pilot/prod |
| SEV-3 | Limited operational issue | import failure, coverage report broken, localized consumer issue | Scheduled response |
| SEV-4 | Low-risk issue | documentation mismatch, non-critical metric missing | Routine correction |

### 31.2. Severity assignment rules

Upgrade severity when:

```text
security/privacy risk exists;
paid access affected;
wrong content delivered;
data integrity uncertain;
restore path uncertain;
issue affects demo credibility with no fallback;
```

### 31.3. SEV-1 mandatory actions

```text
assign incident owner;
notify Project Owner, Technical Lead, Security Owner, Operations Owner;
contain before diagnosing deeply if risk is ongoing;
preserve evidence;
create timeline;
record customer/demo impact;
perform post-incident review;
```

### 31.4. Post-incident review

Post-incident review must include:

```text
what happened;
when it happened;
how detected;
impact;
root cause;
what worked;
what failed;
corrective actions;
owners and due dates;
requirements/docs/tests to update;
```

Blame is not useful. Controls, evidence and learning are useful.

---

## 32. Incident Runbooks

### 32.1. Runbook: API down

Trigger:

```text
readiness false, API 5xx spike, health failure, user reports API unavailable
```

Actions:

```text
1. Check /health and /readiness.
2. Check database connectivity.
3. Check latest deployment/release.
4. Check error logs by request_id/reason_code.
5. If release-related, rollback deployment.
6. If DB-related, enter maintenance/safe mode if needed.
7. Verify health/readiness after fix.
8. Record incident and actions.
```

### 32.2. Runbook: Draft or blocked item delivered

Trigger:

```text
draft_delivery_violations_total > 0, report from user/admin, delivery log shows invalid status
```

Actions:

```text
1. Declare SEV-1 or SEV-2 depending on scope.
2. Pause affected delivery path.
3. Identify item, consumer, delivery_id, selection_request_id.
4. Block affected item if not already blocked.
5. Check status filtering in API/selection.
6. Check whether manual override/demo mode leaked.
7. Audit recent deploys and migrations.
8. Fix and test draft-blocking.
9. Decide whether notification is needed.
10. Record post-incident action: add regression test.
```

### 32.3. Runbook: Telegram duplicate posts

```text
1. Pause affected channel schedule.
2. Identify duplicated delivery/message IDs.
3. Check worker retries and idempotency key.
4. Check Telegram send failure/resend logic.
5. Correct delivery status if needed with audit.
6. Re-enable schedule after test.
7. Record incident and regression test.
```

### 32.4. Runbook: Billing webhook anomaly

```text
1. Pause entitlement updates if compromise suspected.
2. Check webhook signature verification logs.
3. Check event idempotency/replay records.
4. Compare provider events with internal billing_events.
5. Correct entitlements with audit.
6. Reprocess events if safe.
7. Add test for failed condition.
```

### 32.5. Runbook: Import poisoning or bad source

```text
1. Block source or import batch.
2. Stop further imports from source.
3. Identify items created/updated by import_batch_id.
4. Retire/block affected items if needed.
5. Check dry-run/validation reports.
6. Restore or supersede if production data affected.
7. Update parser/manifest rules.
8. Record source decision and release note.
```

### 32.6. Runbook: Backup failure

```text
1. Confirm backup job failure.
2. Check last successful backup timestamp.
3. If no recent valid backup, escalate severity.
4. Fix backup job/storage/config.
5. Run manual backup.
6. Verify artifact/checksum.
7. Schedule restore drill if confidence impacted.
8. Record backup incident.
```

### 32.7. Runbook: Restore failure

```text
1. Do not mark system healthy.
2. Keep or enter maintenance/safe mode.
3. Record failed restore evidence.
4. Check artifact integrity and schema compatibility.
5. Choose earlier backup or alternate restore strategy.
6. Escalate to Technical Lead and Operations Owner.
7. After successful restore, run verification checklist.
```

### 32.8. Runbook: Secret leak

```text
1. Declare security incident.
2. Revoke/rotate affected secret immediately.
3. Audit usage logs.
4. Disable affected consumer/token if needed.
5. Remove secret from repository/history according to secure process.
6. Check CI/no-secrets rules.
7. Notify affected owners if required.
8. Record post-incident actions.
```

---

## 33. Maintenance Mode and Suspension Controls

### 33.1. Maintenance mode purpose

Maintenance mode prevents unsafe operations during deployment, migration, incident or restore.

### 33.2. Maintenance mode capabilities

```text
block public delivery-producing requests;
allow health endpoint;
readiness reports maintenance;
allow admin diagnosis for authorized users;
pause Telegram scheduler;
pause imports;
optionally allow read-only reports;
show machine-readable maintenance reason;
```

### 33.3. Suspension controls

Operations must support suspending:

```text
consumer;
API credential;
Telegram channel schedule;
source file;
import batch;
quiz item;
plan/entitlement;
webhook processing;
worker queue;
```

### 33.4. Suspension record

```text
suspension_id
subject_type
subject_id
reason_code
started_at
started_by
expected_end_at
ended_at
ended_by
incident_id if related
notes
```

---

## 34. Deployment and Release Operations

### 34.1. Release principles

```text
release only after gates pass;
release has version;
release has checklist;
release has rollback path;
release updates docs/contracts if behavior changes;
release records known limitations;
```

### 34.2. Versioning

Recommended application version format:

```text
MAJOR.MINOR.PATCH
```

Recommended release identifiers:

```text
release_id: rel_YYYYMMDD_N
commit_sha: <git sha>
environment: staging/pilot/production
```

### 34.3. Release checklist

Before release:

```text
code merged through approved path;
required CI checks pass;
no-secrets scan passes;
OpenAPI contract updated/validated;
JSON Schema validation passes;
migrations tested;
backup/restore readiness checked if production;
security smoke tests pass;
QA report generated;
known limitations updated;
rollback plan documented;
release owner assigned;
```

During release:

```text
record start time;
deploy version;
run migrations if applicable;
watch health/readiness;
watch logs/errors;
run smoke tests;
```

After release:

```text
record release result;
update changelog;
monitor for error spike;
confirm key flows;
communicate if needed;
```

### 34.4. Deployment modes

| Mode | Use |
|---|---|
| Manual controlled deployment | MVP/demo with documented checklist |
| CI/CD deployment | Pilot/beta/production recommended |
| Blue/green or canary | Future production scale if needed |
| Worker-only deployment | Telegram/billing/import worker updates |
| Data-only release | Source/import/taxonomy/status changes |

### 34.5. Deployment anti-patterns

Forbidden for production:

```text
push directly to production without release record;
deploy without knowing version;
deploy with secrets in repo;
deploy without rollback path;
deploy migration without backup/restore plan;
deploy API behavior change without OpenAPI update;
deploy Telegram worker that reads CSV directly;
```

---

## 35. Rollback and Disable Paths

### 35.1. Rollback principle

Every launch must have an explicit rollback or disable path.

### 35.2. Rollback options

```text
rollback application deployment;
rollback database migration using down migration or restore;
disable feature flag;
disable endpoint;
disable consumer;
pause Telegram scheduler;
revoke API key;
block source;
retire/block quiz item;
revert import manifest change;
restore database backup;
replay billing events after correction;
```

### 35.3. Rollback decision matrix

| Problem | First containment | Possible rollback |
|---|---|---|
| API release breaks next-quiz | Disable release / rollback service | Previous service version |
| Migration corrupts data | Maintenance/safe mode | Restore backup / migration rollback |
| Bad import publishes items | Block source/items | Supersede/retire batch, restore if needed |
| Telegram duplicate sends | Pause scheduler | Worker rollback / idempotency fix |
| Billing webhook grants wrong access | Pause webhook | Revoke entitlements, replay corrected events |
| Security secret leak | Revoke secret | Rotate credentials, invalidate sessions/keys |

### 35.4. Rollback evidence

Record:

```text
rollback_id
trigger
owner
release/version affected
action taken
verification performed
incident link
follow-up tasks
```

---

## 36. CI/CD Operations

### 36.1. CI/CD purpose

CI/CD makes unsafe changes visible before they reach live environments.

### 36.2. Required checks by change type

| Change type | Required checks |
|---|---|
| Documentation | link/path check where feasible, consistency check |
| Data schema | JSON Schema validation, sample item validation |
| Import/parser | import fixture tests, dry-run report test |
| API | OpenAPI validation, contract tests, auth/error tests |
| Selection | unit tests, status/draft exclusion tests, repeat tests |
| Telegram | payload compatibility tests, retry/idempotency tests |
| Billing | webhook signature/idempotency tests, entitlement tests |
| Security | no-secrets scan, authz tests, dependency scan where feasible |
| Database | migration tests, rollback/restore plan for production changes |
| Release candidate | full P0 test suite and QA report |

### 36.3. Protected branch rule

Production-relevant branches should require passing status checks and review before merge.

### 36.4. CI evidence artifacts

```text
CI run ID;
commit SHA;
checks executed;
pass/fail status;
test report;
OpenAPI/schema validation output;
QA report;
security scan output;
```

---

## 37. Configuration and Feature Flags

### 37.1. Configuration principles

```text
configuration is environment-specific;
secrets are not regular config;
config changes are release-relevant when they affect delivery/access/security;
unsafe config must fail readiness;
```

### 37.2. Required configuration categories

```text
environment name;
API base URL;
database connection reference;
queue/cache reference;
Telegram worker enabled/disabled;
Telegram token secret reference;
payment provider mode;
webhook secret reference;
rate limit settings;
maintenance mode flag;
feature flags;
log level;
backup schedule;
```

### 37.3. Feature flags

Recommended flags:

```text
FEATURE_TELEGRAM_DELIVERY
FEATURE_BILLING_WEBHOOKS
FEATURE_PUBLIC_API
FEATURE_ATTEMPTS
FEATURE_ADMIN_IMPORT_COMMIT
FEATURE_DEMO_MODE
FEATURE_MAINTENANCE_MODE
FEATURE_SOURCE_ONBOARDING_WRITE
FEATURE_RATE_LIMITING
```

### 37.4. Feature flag rules

```text
feature flags must have default safe value;
production flag changes must be logged;
flags must not bypass security controls silently;
flags must not make draft items deliverable to normal consumers;
demo mode flag must be clearly visible and isolated;
```

---

## 38. Performance and Capacity Operations

### 38.1. Performance goals

Performance operations must ensure core flows are not obviously unsafe or unusable at MVP/Pilot scale.

### 38.2. Minimum measurements

```text
API next-quiz p50/p95 latency;
selection engine latency;
import dry-run duration;
canonical validation throughput;
coverage report generation time;
Telegram worker job duration;
billing webhook processing latency;
database query latency for critical endpoints;
```

### 38.3. Capacity planning inputs

```text
number of active consumers;
requests per minute;
Telegram posts per day;
quiz items imported;
deliveries per day;
attempts per day;
report generation schedule;
backup size and duration;
```

### 38.4. Scale honesty rule

Do not claim scale readiness without evidence.

Allowed claims must be labeled:

```text
implemented and tested;
implemented but not load-tested;
architecture supports future scale;
planned optimization;
```

---

## 39. Support and Issue Management

### 39.1. Support scope

Support must handle:

```text
API consumer integration issue;
Telegram channel delivery issue;
incorrect quota/access issue;
reported quiz item issue;
source/import issue;
account/API key issue;
security/abuse report;
```

### 39.2. Issue categories

| Category | Owner |
|---|---|
| Content issue | Data/Content Lead |
| API issue | Technical Lead |
| Telegram issue | Operations Owner / Telegram owner |
| Billing/access issue | Billing Owner |
| Security issue | Security Owner |
| Data/report issue | Data/Content Lead / Analytics owner |
| Demo issue | Demo Owner |

### 39.3. Issue severity

| Support severity | Meaning |
|---|---|
| S0 | Security/data exposure/paid access major failure |
| S1 | Public/paid delivery broken or wrong content delivered |
| S2 | Important consumer/channel issue |
| S3 | Non-blocking bug or content report |
| S4 | Question, documentation, enhancement |

### 39.4. Support record fields

```text
issue_id
reported_by
consumer_id if applicable
category
severity
summary
affected_item_id/source_id/delivery_id if applicable
time_reported
owner
status
resolution
linked_incident_id
```

---

## 40. Operational Data Privacy

### 40.1. Privacy principle

Store only what is needed for authentication, delivery, attempts, billing/entitlements, abuse prevention, support and analytics.

### 40.2. Data minimization in operations

Operations should avoid storing:

```text
unnecessary learner identity;
full payment data;
raw secrets;
excessive Telegram user data;
private source content in logs;
correct answer keys in learner-facing contexts;
```

### 40.3. Safe analytics

Analytics should aggregate where possible:

```text
by consumer;
by level;
by theme;
by delivery status;
by quota plan;
by time bucket;
```

Detailed user/learner analytics require explicit privacy/legal review appropriate to deployment context.

### 40.4. Data deletion/retention questions

Future privacy/compliance document must decide:

```text
retention of attempts;
retention of delivery logs;
retention of support requests;
retention of billing/customer records;
user deletion requests;
school/student data processing;
EU/GDPR posture;
```

---

## 41. Operational Evidence Model

### 41.1. Evidence artifacts

Operations must produce or preserve:

```text
release checklist;
QA release report;
health/readiness sample;
backup metadata;
restore_run report;
incident record;
post-incident review;
source onboarding report;
import report;
coverage report;
delivery log sample;
quota denial sample;
security smoke test output;
CI run output;
launch approval record;
known limitations register;
```

### 41.2. Evidence storage

Recommended paths:

```text
reports/releases/
reports/imports/
reports/coverage/
reports/operations/
reports/incidents/
reports/restore/
reports/demo/
```

### 41.3. Evidence naming

```text
release_YYYYMMDD_<env>_<version>.md
restore_YYYYMMDD_<env>_<backup_id>.md
incident_INC-YYYYMMDD-001.md
import_<import_batch_id>.md
coverage_YYYYMMDD.md
demo_run_YYYYMMDD.md
```

### 41.4. Evidence honesty rule

Evidence must not be fabricated. Simulated evidence is allowed only if clearly labelled as simulated.

---

## 42. Stanford-Style Demo Operations

### 42.1. Demo operations thesis

The Stanford-style demo must show a governed operational platform, not a set of claims.

### 42.2. Demo preflight checklist

Before demo:

```text
demo environment identified;
demo credentials are safe;
no production secrets visible;
demo data labelled;
corpus snapshot report ready;
source onboarding report ready;
canonical validation report ready;
API endpoint tested;
delivery log sample ready;
negative control tested;
Telegram dry-run or controlled send tested;
analytics snapshot ready;
known limitations sheet ready;
fallback artifacts prepared;
```

### 42.3. Demo fallback artifacts

If live demo fails, show:

```text
recorded API request/response;
OpenAPI excerpt;
source onboarding report;
dry-run import report;
delivery log excerpt;
Telegram simulated payload;
coverage report;
QA gate summary;
architecture diagram;
incident/operations plan excerpt;
```

### 42.4. Demo safety rules

```text
no secrets on screen;
no private learner/billing data;
no production admin tokens;
no unsupported claims;
clearly label simulated vs live;
show at least one negative control;
```

### 42.5. Demo operations evidence

Demo owner must record:

```text
demo_run_id
date
environment
version
script version
checks passed
known limitations
fallback artifacts
result
follow-up tasks
```

---

## 43. Launch Gates — Operations

### 43.1. MVP operations gate

MVP operations gate passes when:

```text
OPS-MVP-001  Basic runbook exists.
OPS-MVP-002  Health command/endpoint or equivalent exists.
OPS-MVP-003  Import/API/delivery logs exist for demo flow.
OPS-MVP-004  Source onboarding report can be generated or demonstrated.
OPS-MVP-005  Delivery/reservation log can be shown.
OPS-MVP-006  Known limitations are documented.
OPS-MVP-007  Rollback/disable notes exist for demo/MVP.
OPS-MVP-008  Demo preflight checklist exists.
```

### 43.2. Closed pilot operations gate

Closed pilot gate passes when:

```text
OPS-PILOT-001  Staging/pilot environment is identified.
OPS-PILOT-002  Health/readiness checks exist.
OPS-PILOT-003  Monitoring/logging exists for API and workers.
OPS-PILOT-004  Backup process exists for pilot data.
OPS-PILOT-005  Restore procedure exists.
OPS-PILOT-006  Incident playbook exists.
OPS-PILOT-007  Telegram delivery failures are observable.
OPS-PILOT-008  Consumer disable path exists.
OPS-PILOT-009  Support/issue path exists.
```

### 43.3. Public beta operations gate

Public beta gate passes when:

```text
OPS-BETA-001  Rate limits or usage controls are operational.
OPS-BETA-002  Alerts or monitored operational review exists.
OPS-BETA-003  Backup schedule is automated or reliably controlled.
OPS-BETA-004  Restore drill evidence exists.
OPS-BETA-005  Incident severity and escalation model exists.
OPS-BETA-006  Release/rollback process exists.
OPS-BETA-007  Security operations baseline exists.
OPS-BETA-008  Privacy/legal review appropriate to beta scope completed.
```

### 43.4. Production operations gate

Production gate passes when:

```text
OPS-PROD-001  CI/CD or controlled deployment process exists.
OPS-PROD-002  Backups exist and are monitored.
OPS-PROD-003  Restore drill completed and recorded.
OPS-PROD-004  Monitoring dashboard exists.
OPS-PROD-005  Critical alerts or owner review process exists.
OPS-PROD-006  Incident playbook exists and owner assigned.
OPS-PROD-007  Rollback/disable paths verified.
OPS-PROD-008  Data migrations are versioned and tested.
OPS-PROD-009  Security baseline implemented.
OPS-PROD-010  Support/contact path exists.
OPS-PROD-011  Launch risks and limitations are documented.
OPS-PROD-012  Launch approval is recorded.
```

### 43.5. Stanford-ready operations gate

Stanford-ready operations gate passes when:

```text
OPS-DEMO-001  Demo environment prepared.
OPS-DEMO-002  Demo data safe and labelled.
OPS-DEMO-003  Demo credentials non-production or clearly controlled.
OPS-DEMO-004  Health/readiness or equivalent operational proof available.
OPS-DEMO-005  Backup/restore plan summarized.
OPS-DEMO-006  Incident/rollback plan summarized.
OPS-DEMO-007  Source onboarding operational path shown.
OPS-DEMO-008  Delivery log and negative control shown.
OPS-DEMO-009  Known limitations shown honestly.
OPS-DEMO-010  Fallback artifacts ready.
```

---

## 44. Operations Requirements

### 44.1. Requirement ID system

Operations requirements use:

```text
OPS-<AREA>-<NUMBER>
```

Areas:

```text
GOV       governance
ENV       environments
HLT       health/readiness
OBS       observability
LOG       logging/audit
BKP       backup
RST       restore
INC       incident response
REL       release/deployment
RLB       rollback/disable
SRC       source/import operations
API       API operations
TG        Telegram operations
BILL      billing/entitlement operations
SEC       security operations
DEMO      Stanford demo operations
SUP       support
```

### 44.2. Core operations requirements

| ID | Requirement | Priority | Phase | Verification |
|---|---|---:|---|---|
| OPS-GOV-001 | The project SHALL assign an Operations Owner before closed pilot. | P0 | Pilot | I |
| OPS-GOV-002 | Production launch SHALL require launch approval record. | P0 | Prod | I |
| OPS-ENV-001 | The project SHALL distinguish demo/staging/pilot/production environments. | P0 | Pilot | I/D |
| OPS-ENV-002 | Demo credentials SHALL NOT work in production. | P0 | Demo/Pilot | I/T |
| OPS-HLT-001 | API SHALL provide health or equivalent operational check. | P1 | MVP/Pilot | T/D |
| OPS-HLT-002 | API SHALL provide readiness or equivalent dependency check before pilot. | P1 | Pilot | T/D |
| OPS-OBS-001 | System SHALL expose/log core metrics for API, selection, delivery and imports. | P1 | Pilot | A/I |
| OPS-LOG-001 | Critical operations SHALL produce structured logs with correlation IDs where feasible. | P1 | Pilot | I/T |
| OPS-LOG-002 | Logs SHALL NOT expose raw secrets/tokens. | P0 | MVP | I/T |
| OPS-BKP-001 | The system SHALL have backup procedure before production launch. | P0 | Prod | I/O |
| OPS-BKP-002 | Production backups SHALL record metadata and success/failure status. | P0 | Prod | I/O |
| OPS-RST-001 | Restore procedure SHALL exist before production launch. | P0 | Prod | I/O |
| OPS-RST-002 | Restore drill SHALL be completed or equivalent evidence recorded before production claim. | P0 | Prod | O |
| OPS-INC-001 | Incident playbook SHALL exist before production launch. | P0 | Prod | I |
| OPS-INC-002 | Incidents SHALL have owner, severity, affected component and action log. | P1 | Pilot/Prod | I |
| OPS-REL-001 | Release checklist SHALL exist for pilot and production. | P1 | Pilot | I |
| OPS-REL-002 | Production deployment SHALL have rollback/disable path. | P0 | Prod | I/O |
| OPS-SRC-001 | Source onboarding operations SHALL require source_id, checksum, inventory and manifest before import. | P0 | MVP | I/D |
| OPS-SRC-002 | Dry-run import SHALL produce report before production-relevant import. | P0 | MVP | D/A |
| OPS-API-001 | API deployment smoke tests SHALL verify no draft/blocked item delivery. | P0 | MVP/Pilot | T/D |
| OPS-TG-001 | Telegram worker SHALL be pausable by channel and globally. | P1 | Pilot | D/T |
| OPS-TG-002 | Telegram failures SHALL be logged and observable. | P1 | Pilot | T/D |
| OPS-BILL-001 | Billing webhook failures and signature failures SHALL be logged. | P1 | Beta | T/D |
| OPS-BILL-002 | Manual entitlement overrides SHALL be audited. | P0 | Pilot/Beta | T/I |
| OPS-SEC-001 | Secret rotation procedure SHALL exist before public beta. | P1 | Beta | I |
| OPS-DEMO-001 | Demo operations checklist SHALL exist before Stanford-style demo. | P0 | Demo | I |
| OPS-DEMO-002 | Demo SHALL have fallback artifacts for critical proof points. | P1 | Demo | I |
| OPS-SUP-001 | Support/issue reporting path SHALL exist before public beta/production. | P1 | Beta/Prod | I/D |

---

## 45. Runbook Catalog

### 45.1. Required runbooks

| Runbook | Priority | Phase |
|---|---:|---|
| `runbooks/health_readiness.md` | P1 | Pilot |
| `runbooks/deploy_release.md` | P1 | Pilot |
| `runbooks/rollback.md` | P0 | Production |
| `runbooks/backup.md` | P0 | Production |
| `runbooks/restore.md` | P0 | Production |
| `runbooks/incident_response.md` | P0 | Production |
| `runbooks/source_onboarding.md` | P0 | MVP/Pilot |
| `runbooks/import_dry_run.md` | P0 | MVP |
| `runbooks/api_smoke_test.md` | P0 | MVP/Pilot |
| `runbooks/telegram_delivery.md` | P1 | Pilot |
| `runbooks/billing_webhook.md` | P1 | Beta |
| `runbooks/secret_rotation.md` | P1 | Beta |
| `runbooks/demo_preflight.md` | P0 | Demo |
| `runbooks/support_triage.md` | P1 | Beta |

### 45.2. Runbook template

```markdown
# Runbook: <name>

## Purpose

## Owner

## Trigger

## Preconditions

## Severity / risk

## Steps

## Verification

## Rollback / abort path

## Evidence to record

## Escalation

## Related requirements / use cases

## Last reviewed
```

---

## 46. Operational Risk Register

| Risk ID | Risk | Impact | Control |
|---|---|---|---|
| OPS-RISK-001 | Backup exists but restore fails | Data loss / false readiness | Restore drills and verification checklist |
| OPS-RISK-002 | Telegram worker duplicates posts | Channel trust damage | Idempotency, delivery log, pause control |
| OPS-RISK-003 | Draft item delivered | Product trust/severity incident | Status filters, tests, metric, incident runbook |
| OPS-RISK-004 | Bad import corrupts corpus | Data integrity | Dry-run, validation, import batch rollback/block |
| OPS-RISK-005 | Billing webhook grants wrong access | Revenue/trust/security | Signature verification, idempotency, audit |
| OPS-RISK-006 | Secret committed | Security incident | No-secrets scan, rotation runbook |
| OPS-RISK-007 | No owner during incident | Slow recovery | RACI, incident owner rule |
| OPS-RISK-008 | Demo live failure | Presentation credibility | Preflight and fallback artifacts |
| OPS-RISK-009 | Metrics/logs unavailable | Poor diagnosis | Basic observability and evidence retention |
| OPS-RISK-010 | Scale overclaim | Trust loss | Label implemented/tested/planned honestly |
| OPS-RISK-011 | Source file added ad hoc | Future data chaos | Source onboarding operations gate |
| OPS-RISK-012 | Manual DB edit breaks traceability | Data/audit risk | Emergency change rule and audit log |

---

## 47. Traceability Matrix

| Operational area | Vision/Product/SRS link | Use cases | QA / evidence |
|---|---|---|---|
| Operational trust | VOBJ-010, AC-PROD-001–012 | UC-014, UC-015 | QA-OPS, restore_run, release report |
| Future source onboarding | VOBJ-012, SRS-ONB/SRC/IMP | UC-001, UC-002, UC-030 | source onboarding report, dry-run report |
| API delivery operations | VOBJ-003, SRS-API/SEL | UC-005, UC-008, UC-019 | API smoke tests, delivery log |
| Telegram operations | SRS-TG, Product Telegram gate | UC-007, UC-021, UC-022 | Telegram delivery logs, dry-run evidence |
| Backup/restore | SRS-DOC-008, NFR-OPS, NFR-REL | UC-014 | restore drill report |
| Security operations | Security threat model, NFR-SEC | UC-024, UC-013 | security logs, secret rotation evidence |
| Billing/entitlements | VOBJ-009, SRS-BILL | UC-008, UC-013, UC-023 | quota denial, webhook logs |
| Demo operations | VOBJ-011, SRS-DEMO | UC-015, UC-030 | demo_run report, fallback artifacts |

---

## 48. MVP / Pilot / Beta / Production Operations Cut

### 48.1. MVP operations cut

MVP may be accepted with:

```text
manual deployment;
manual backup notes;
manual restore procedure draft;
logs visible locally/demo;
source/import reports;
API smoke tests;
demo fallback artifacts;
known limitations;
```

MVP may not claim:

```text
high availability;
production-grade SLA;
fully automated incident response;
full billing operations;
enterprise compliance;
```

### 48.2. Closed pilot operations cut

Closed pilot requires:

```text
real pilot environment;
basic monitoring/logging;
backup process;
restore procedure;
Telegram/API failure logging;
incident path;
consumer disable path;
support contact;
```

### 48.3. Public beta operations cut

Public beta requires:

```text
rate limits/usage controls;
security monitoring;
restore drill evidence;
release/rollback process;
support/abuse path;
privacy/legal baseline;
```

### 48.4. Production operations cut

Production requires:

```text
controlled deployment;
versioned migrations;
monitored backups;
restore drill;
incident playbook;
alerts or defined owner review;
security operations;
support path;
launch approval;
```

---

## 49. Operational Checklists

### 49.1. Daily pilot review checklist

```text
[ ] API health/readiness ok
[ ] worker heartbeat ok
[ ] last backup status ok
[ ] no draft delivery violations
[ ] no unexplained Telegram failures
[ ] no unexplained quota/entitlement anomalies
[ ] no auth/security spikes
[ ] no failed import/report jobs
[ ] open incidents reviewed
[ ] known limitations unchanged or updated
```

### 49.2. Pre-release checklist

```text
[ ] release version identified
[ ] CI checks passed
[ ] QA report generated
[ ] schema/OpenAPI changes documented
[ ] migration tested
[ ] backup verified or created
[ ] rollback path documented
[ ] smoke tests defined
[ ] release notes updated
[ ] known limitations updated
[ ] owner assigned
```

### 49.3. Post-release checklist

```text
[ ] health ok
[ ] readiness ok
[ ] API smoke test passed
[ ] draft-blocking test passed
[ ] delivery log created
[ ] quota denial test passed or unchanged
[ ] Telegram dry-run/worker check passed if relevant
[ ] error rate normal
[ ] release record completed
```

### 49.4. Pre-demo checklist

```text
[ ] demo environment works
[ ] demo credentials safe
[ ] no secrets visible
[ ] corpus snapshot ready
[ ] source onboarding artifact ready
[ ] canonical validation artifact ready
[ ] API request/response tested
[ ] delivery log ready
[ ] negative control tested
[ ] Telegram dry-run/controlled delivery ready
[ ] fallback artifacts ready
[ ] limitations sheet ready
```

### 49.5. Backup checklist

```text
[ ] backup job completed
[ ] artifact exists
[ ] checksum/metadata recorded
[ ] retention date known
[ ] alert/log produced
[ ] restore drill status known
```

### 49.6. Restore checklist

```text
[ ] restore owner assigned
[ ] backup artifact selected
[ ] artifact integrity checked
[ ] restored to safe target
[ ] migrations verified
[ ] consistency checks passed
[ ] health/readiness passed
[ ] API smoke test passed
[ ] delivery/entitlement history verified
[ ] restore_run report recorded
```

---

## 50. Operations Report Template

```markdown
# Operations Readiness Report

## 1. Scope

Environment:
Version:
Date:
Owner:

## 2. Summary

Ready / Not Ready / Ready with limitations

## 3. Health and readiness

## 4. Deployment/release status

## 5. Backup status

## 6. Restore drill status

## 7. Monitoring/logging status

## 8. Incident readiness

## 9. Security operations summary

## 10. API/Telegram/Billing operational checks

## 11. Data/source/import checks

## 12. Open incidents and risks

## 13. Known limitations

## 14. Evidence artifacts

## 15. Decision and approval
```

---

## 51. Open Operations Questions

These questions should be resolved during implementation planning:

1. Which hosting/runtime environment will be used first: local Docker Compose, managed PaaS, VPS, cloud containers or Kubernetes?
2. Which database backup mechanism will be used for demo, pilot and production?
3. What is the exact first RPO/RTO target for paid launch?
4. Which observability stack will be used: provider-based, OpenTelemetry pipeline, cloud-native logs, or simple MVP logs first?
5. Who is the first named Operations Owner?
6. What channel is used for operational alerts: email, Telegram admin chat, Slack, GitHub issues or provider alerts?
7. What is the first real Telegram channel or only simulated demo consumer?
8. Which billing provider, if any, is used during pilot?
9. What support/contact path exists for API consumers and Telegram channel owners?
10. How long should delivery logs and attempt logs be retained?
11. What privacy/legal posture applies to EU learners and schools?
12. What level of production SLA will be promised, if any?
13. What data subset is safe for Stanford-style demo?
14. Should restore drills be scheduled monthly, per release, or before each launch stage?
15. Which operational dashboards are mandatory before public beta?

---

## 52. Acceptance Criteria for This Document

This document is accepted when it:

```text
AC-OPS-DOC-001  Aligns with Constitution, Vision, Charter, SRS, Use Cases, Domain Model, Architecture, Data/API Standards, Security and QA.
AC-OPS-DOC-002  Defines operational principles and roles.
AC-OPS-DOC-003  Defines environment model.
AC-OPS-DOC-004  Defines health/readiness expectations.
AC-OPS-DOC-005  Defines metrics/logging/alerting standards.
AC-OPS-DOC-006  Defines backup and restore policy.
AC-OPS-DOC-007  Defines incident response model.
AC-OPS-DOC-008  Defines release/deployment/rollback rules.
AC-OPS-DOC-009  Defines source/import, API, Telegram and billing operations.
AC-OPS-DOC-010  Defines launch gates for MVP/Pilot/Beta/Production/Stanford demo.
AC-OPS-DOC-011  Defines operational evidence model.
AC-OPS-DOC-012  Lists remaining documents needed for the project.
```

---

## 53. Reference Standards and Alignment

This document aligns with the following standards and engineering practices. These references guide the operational model; implementation should verify exact versions during build/release.

### 53.1. Stanford/SLAC-style requirements discipline

API Quiz Bank uses a Stanford/SLAC-style engineering approach:

```text
vision → requirements → use cases → architecture → contracts → tests → operations → demo evidence
```

Operations extends this chain into:

```text
runbooks → monitoring → backup/restore → incident response → release gates → evidence
```

### 53.2. SRE concepts

SLO/SLI/error-budget thinking is used internally to make reliability measurable, not to overpromise contractual SLA.

### 53.3. OpenTelemetry-style observability

Metrics, logs and traces should be correlated through request IDs, resources and attributes where feasible.

### 53.4. NIST incident response alignment

Incident response aligns with current NIST incident-response thinking: preparation, detection, response, recovery and continuous improvement integrated into risk management.

### 53.5. PostgreSQL backup and recovery

Production database operations should support regular backups, WAL/PITR or equivalent recovery strategy where feasible, and restore tests before production claims.

### 53.6. OWASP API security alignment

Operations must monitor and control API object-level authorization, authentication, resource consumption, endpoint inventory and security misconfiguration risks.

### 53.7. GitHub / protected branch discipline

Repository operations should require protected branches and status checks for production-relevant changes where possible.

### 53.8. NIST SSDF alignment

Secure software operations should include development/release controls, vulnerability mitigation practices, security review and evidence-based change management.

---

## 54. Final Operations Rule

```text
API Quiz Bank is operations-ready only when the team can show, with evidence:

what is deployed,
what data is active,
which consumers can receive content,
which statuses are deliverable,
which sources are active,
which imports changed the corpus,
which deliveries happened,
which entitlements allowed access,
which failures occurred,
which backups exist,
how restore works,
how incidents are handled,
how releases are rolled back,
how new files are onboarded,
and how a Stanford-style reviewer can verify all of it without relying on trust alone.
```

---

## 55. Remaining Documents to Create

The documentation foundation is now strong, but the platform still needs specialized documents and implementation artifacts.

### 55.1. High-priority next documents

| Order | Document | Purpose | Priority |
|---:|---|---|---:|
| 1 | `docs/11_billing_model.md` | Plans, customers, entitlements, quotas, usage, manual overrides, payment-provider-neutral model | P0/P1 |
| 2 | `docs/12_analytics_model.md` | Corpus, delivery, attempt, business, operations analytics and dashboards | P1 |
| 3 | `docs/13_stanford_presentation_outline.md` | Stanford-style demo narrative, slide structure, proof artifacts, Q&A defense | P0/P1 |
| 4 | `docs/14_roadmap.md` | Phase plan from governance foundation to MVP, pilot, beta and production | P1 |
| 5 | `docs/15_repository_governance.md` | Git, branches, CODEOWNERS, PR rules, changelog, release/versioning discipline | P1 |
| 6 | `docs/16_source_onboarding_playbook.md` | Practical playbook for adding future quiz files safely | P0 |
| 7 | `docs/17_admin_workflow.md` | Admin operations: import, review, approve, publish, retire, block, consumer controls | P1 |
| 8 | `docs/18_telegram_delivery_playbook.md` | Telegram scheduling, dry-run, sendPoll compatibility, retries, channel operations | P1 |
| 9 | `docs/19_privacy_compliance.md` | Privacy, retention, learner/school data, EU/GDPR posture, logging limits | P1/P2 |

### 55.2. Required machine-readable artifacts

| Artifact | Purpose | Priority |
|---|---|---:|
| `data/manifests/file_inventory.csv` | Current and future source inventory | P0 |
| `data/manifests/import_manifest.yml` | Source → parser/defaults/status mapping | P0 |
| `data/taxonomy/topics.yml` | 18 canonical themes | P0 |
| `data/taxonomy/cefr_levels.yml` | CEFR level definitions | P0 |
| `data/taxonomy/objectives.yml` | Objective IDs and meanings | P1 |
| `data/taxonomy/patterns.yml` | Pattern IDs and meanings | P1 |
| `data/schemas/quiz_item.schema.json` | Canonical quiz item JSON Schema | P0 |
| `data/schemas/import_manifest.schema.json` | Manifest validation schema | P1 |
| `api/openapi.yaml` | Versioned API contract | P0 |
| `database/migrations/` | Versioned database migrations | P0 |
| `database/indexes.sql` | Initial critical indexes | P1 |

### 55.3. Required runbooks

| Runbook | Priority |
|---|---:|
| `runbooks/source_onboarding.md` | P0 |
| `runbooks/import_dry_run.md` | P0 |
| `runbooks/api_smoke_test.md` | P0 |
| `runbooks/demo_preflight.md` | P0 |
| `runbooks/backup.md` | P0/P1 |
| `runbooks/restore.md` | P0/P1 |
| `runbooks/incident_response.md` | P0/P1 |
| `runbooks/deploy_release.md` | P1 |
| `runbooks/rollback.md` | P1 |
| `runbooks/telegram_delivery.md` | P1 |
| `runbooks/billing_webhook.md` | P1/P2 |
| `runbooks/secret_rotation.md` | P1/P2 |

### 55.4. Required reports and evidence templates

| Template | Priority |
|---|---:|
| `reports/templates/import_report.md` | P0 |
| `reports/templates/source_onboarding_report.md` | P0 |
| `reports/templates/coverage_report.md` | P1 |
| `reports/templates/release_qa_report.md` | P1 |
| `reports/templates/operations_readiness_report.md` | P1 |
| `reports/templates/restore_run_report.md` | P1 |
| `reports/templates/incident_report.md` | P1 |
| `reports/templates/demo_run_report.md` | P0/P1 |

### 55.5. Recommended repository governance files

| File | Purpose | Priority |
|---|---|---:|
| `SECURITY.md` | Security reporting and handling | P1 |
| `CONTRIBUTING.md` | Contribution/change rules | P1 |
| `CODEOWNERS` | Ownership and review routing | P1 |
| `CHANGELOG.md` | Release history | P1 |
| `.github/workflows/quality.yml` | CI quality checks | P1 |
| `.github/dependabot.yml` or equivalent | Dependency/security update policy | P2 |

### 55.6. Suggested next step

The next most logical document is:

```text
docs/11_billing_model.md
```

Reason:

```text
The platform already has data, API, security, QA and operations standards.
Billing/entitlements is the next major product-control layer before paid access,
Telegram channel monetization, API plans, school packages and Stanford-style business narrative.
```
