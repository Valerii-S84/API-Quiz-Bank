# API Quiz Bank — Analytics Model

**Документ:** `docs/12_analytics_model.md`  
**Назва проєкту:** API Quiz Bank  
**Внутрішня історична назва:** QuizBank / German QuizBank Platform  
**Версія:** 1.0.0  
**Статус:** foundational analytics, reporting and demo-evidence model; subordinate to `CONSTITUTION.md`; aligned with `00_vision.md`–`11_billing_model.md`  
**Дата:** 2026-05-07  
**Мова:** українська з канонічними технічними термінами англійською  
**Власник:** project owner / authorized analytics maintainer  
**Керівні документи:** `CONSTITUTION.md`, `docs/00_vision.md`, `docs/01_product_charter.md`, `docs/02_requirements_srs.md`, `docs/03_use_cases.md`, `docs/04_domain_model.md`, `docs/05_architecture.md`, `docs/06_data_standard.md`, `docs/07_api_standard.md`, `docs/08_security_threat_model.md`, `docs/09_quality_assurance.md`, `docs/10_operations.md`, `docs/11_billing_model.md`  
**Наступні документи:** `13_stanford_presentation_outline.md`, `14_roadmap.md`, `15_repository_governance.md`, `16_source_onboarding_playbook.md`, `17_admin_workflow.md`, `18_telegram_delivery_playbook.md`, `19_privacy_compliance.md`

---

## 0. Executive Summary

`12_analytics_model.md` визначає, як **API Quiz Bank** перетворює corpus state, delivery events, attempts, usage, quality signals and operational facts на керовані analytics, reports, dashboards and demo evidence.

Головна теза документа:

```text
Facts are recorded.
Reports are derived.
Metrics are explained.
Access is scoped.
Demo evidence is reproducible.
```

Analytics у цьому проєкті існує не для красивих скриншотів. Воно існує, щоб відповідати на critical product questions:

```text
Що реально є в corpus?
Що з цього можна видавати?
Що кому видано?
Які item-и працюють погано?
Які спроби, quality signals and reports накопичуються?
Як споживаються quotas and entitlements?
Наскільки надійні API, Telegram and operations?
Які твердження можна чесно показати в Stanford-style demo?
```

Правильний analytics flow:

```text
source files / import runs / statuses
  → canonical database records
  → delivery / attempt / usage / report / ops events
  → aggregate views / generated reports / dashboards
  → product decisions / quality actions / billing support / demo evidence
```

Неправильний flow:

```text
manual spreadsheet
  → ad hoc counts
  → screenshots
  → unverifiable demo claims
  → broken trust
```

Foundational doc set currently uses this baseline:

```text
115 active bank files
30,974 active rows/items
CEFR levels: A1, A2, B1, B2, C1, C2
18 canonical themes
all active items currently in draft operational status
local constitution check: violations=0 for 30,974 rows
```

Analytics model must remain snapshot-aware. Generated analytics may later reflect newer corpus states, but every report must clearly identify its own snapshot, generation time and input set.

Analytics scope in this document covers:

```text
corpus analytics
coverage analytics
delivery analytics
attempt analytics
billing/usage analytics
quality analytics
operational analytics
Stanford demo metrics
```

Final rule:

```text
API Quiz Bank must not claim analytics insight, business value or Stanford-style readiness
unless the underlying facts, scope, freshness, authorization and limitations are explicit.
```

---

## 1. Role of This Document

### 1.1. Мета документа

`12_analytics_model.md` відповідає на питання:

```text
Що вважається analytics fact, derived metric, generated report and dashboard?
Які data sources є канонічними для analytics?
Як розділяються corpus, delivery, attempt, billing, quality and ops analytics?
Які privacy and authorization boundaries застосовуються?
Які metrics потрібні для MVP, Pilot, Beta, Production and Stanford demo?
Які reports повинні бути reproducible?
Які signals повинні вести до quality review or operational action?
Які anti-patterns роблять analytics недійсним?
```

### 1.2. Місце в документаційній ієрархії

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
docs/11_billing_model.md
  ↓
docs/12_analytics_model.md
  ↓
implementation / report jobs / dashboards / admin / demo evidence
```

### 1.3. Що цей документ робить

Цей документ визначає:

```text
analytics thesis
analytics scope and boundaries
vocabulary and source-of-truth hierarchy
event and report model
metric catalog
report catalog
privacy/authorization rules
freshness and retention expectations
analytics API/admin surface
data model seeds
integration points
QA and launch gates
traceability
risk register
Stanford demo evidence
```

### 1.4. Що цей документ не робить

Цей документ НЕ є:

```text
повним BI-tool manual;
final Grafana/Metabase configuration;
machine-learning specification;
learning-science research paper;
privacy policy;
final warehouse schema;
гарантією персоналізованих learner analytics у MVP;
дозволом показувати private or cross-consumer data in demos.
```

---

## 2. Stanford-Style Analytics Discipline

У межах API Quiz Bank “Stanford-style analytics” означає не бренд і не формальне схвалення Stanford. Це означає інженерну discipline level, де кожен analytics claim має traceability:

```text
product question
  → source facts
  → metric definition
  → calculation boundary
  → access scope
  → report or dashboard
  → QA evidence
  → demo evidence
```

### 2.1. Analytics quality attributes

Analytics model має бути:

| Attribute | Meaning |
|---|---|
| Traceable | Кожен metric/report можна звести до canonical records or generated inputs. |
| Reproducible | Один і той самий snapshot дає той самий result або фіксує input drift. |
| Scoped | Consumer/user/organization visibility строго обмежена authorization scope. |
| Explainable | Пояснено, що metric рахує, чого не рахує і які має caveats. |
| Actionable | Analytics підтримує quality, operations, billing or product decisions. |
| Honest | Demo/report не видає planned analytics за implemented analytics. |
| Freshness-aware | Старі reports не маскуються під near-real-time. |
| Safe | Analytics не ламає privacy, secrets or object-level authorization. |

### 2.2. Analytics verification rule

Bad analytics statement:

```text
Users are learning better.
```

Good analytics statement:

```text
For consumer_type=telegram_channel over the selected date range, delivered published items
produced 1,250 recorded attempts, median correctness 71%, median response time 14.2s,
and 0 repeat-policy violations in the report snapshot generated at 2026-05-07T18:20:00Z.
```

### 2.3. Analytics is part of trust, not decoration

Якщо analytics не спирається на canonical facts, не розрізняє statuses, змішує production and demo data або порушує auth boundaries, то це не insight. Це compliance and credibility defect.

---

## 3. Core Analytics Thesis

### 3.1. Product analytics statement

```text
API Quiz Bank measures governed content readiness, governed delivery behavior,
governed user interaction and governed operational reliability.
```

### 3.2. Analytics exists for controlled decisions

Analytics має підтримувати:

```text
coverage decisions
publication decisions
consumer reliability review
quality review
billing/usage support
operational readiness
Stanford demo evidence
```

### 3.3. Analytics must not distort content governance

Analytics MUST NOT:

```text
promote draft items to production readiness by popularity alone;
override blocked/retired status;
treat payment-provider status as canonical entitlement truth;
hide report generation limitations;
invent learner insight without attempt evidence;
mix demo/test activity with production analytics without clear labels.
```

---

## 4. Non-Negotiable Analytics Rules

1. Analytics MUST derive from canonical database facts, generated reports or immutable events, not from ad hoc manual counts.
2. Analytics MUST distinguish corpus existence from production eligibility.
3. Delivery analytics MUST preserve consumer/channel context.
4. Attempt analytics MUST attach to delivered item/version context where available.
5. Billing/usage analytics MUST use internal entitlement/quota/usage records, not payment-provider state alone.
6. Analytics MUST respect object-level authorization and role scope.
7. Generated reports MUST record snapshot metadata and limitations.
8. Demo analytics MUST be reproducible and clearly marked as demo, pilot or production evidence.
9. Quality analytics MUST support review/status workflow, not bypass it.
10. Operational analytics MUST be actionable enough to support incident, launch and rollback decisions.

---

## 5. Analytics Scope

### 5.1. Included analytics domains

This document covers:

```text
corpus analytics
coverage analytics
delivery analytics
attempt analytics
billing and usage analytics
quality analytics
operational analytics
security/audit summary analytics
Stanford demo analytics
```

### 5.2. Out of scope for this document

This document does not define:

```text
full adaptive-learning recommendation engine;
production data warehouse vendor choice;
statistical significance policy for pedagogy claims;
full ML difficulty model;
school-gradebook export standard;
public marketing KPI taxonomy.
```

---

## 6. Key Analytics Questions

Analytics in API Quiz Bank must be able to answer at least these questions:

### 6.1. Corpus and coverage

```text
How many active items exist?
How many items are draft / approved / published / blocked / retired?
What is the level × theme × objective × pattern coverage?
Which themes or levels are under-covered?
Which new sources changed coverage?
```

### 6.2. Delivery and attempts

```text
What was delivered to which consumer?
What failed to deliver and why?
Which items are repeated too often or not enough?
Which consumers are active?
Which attempt flows exist and what outcomes do they produce?
```

### 6.3. Quality and reporting

```text
Which items get wrong-answer reports?
Which items have abnormal correctness or timing?
Which items moved to monitored or needs_review?
Which sources/imports correlate with quality anomalies?
```

### 6.4. Billing and usage

```text
What quotas were consumed?
Which access denials came from entitlement vs quota vs auth?
Which plans/features are actually used?
What evidence supports invoice, support or dispute questions?
```

### 6.5. Operations and demo

```text
How healthy are report jobs and dashboards?
How fresh is each report?
How reliable is Telegram delivery?
What can be shown honestly in Stanford-style presentation?
```

---

## 7. Actors and Stakeholders

| Actor | Analytics need |
|---|---|
| Product Owner | Coverage, delivery, usage, quality and demo readiness |
| Content / Data Lead | Coverage gaps, source/import health, quality flags |
| Engineering Maintainer | Report correctness, data freshness, failures, performance |
| Operations Owner | Delivery success/failure, report freshness, run health |
| Billing Owner | Usage, quota consumption, denials, plan utilization |
| Teacher / School | Scoped class/group analytics only |
| API Client / Consumer Owner | Scoped delivery/usage analytics only |
| Security Owner | Access violations, report exposure risks, audit summaries |
| Demo Owner | Safe, reproducible, explainable evidence artifacts |

---

## 8. Core Analytics Vocabulary

| Term | Meaning |
|---|---|
| `analytics_fact` | Canonical stored fact or immutable event used as analytics input. |
| `derived_metric` | Calculated value derived from facts under a defined formula and scope. |
| `analytics_report` | Structured generated analytics output with metadata. |
| `dashboard_view` | Human-facing grouped representation of one or more reports/metrics. |
| `snapshot_time` | The effective data cutoff used to produce a report. |
| `freshness` | How recent report data is relative to expected SLA/SLO. |
| `scope` | Global, organization, consumer, channel, user, theme, level, item or date range boundary. |
| `demo_evidence` | Safe artifact that supports Stanford-style demonstration claim. |
| `quality_signal` | Report, correctness anomaly, failure trend or metadata-driven concern. |
| `authorized_projection` | Analytics projection filtered by role, ownership, entitlement and privacy rules. |

---

## 9. Analytics Objectives and Consumer Types

### 9.1. Internal product analytics

Primary goals:

```text
content readiness
coverage completeness
delivery reliability
quality triage
billing and quota understanding
launch and demo evidence
```

### 9.2. Consumer-facing analytics

Allowed only through scoped projections:

```text
teacher/classroom delivery summary
organization usage summary
API client usage summary
personal progress summary where attempts exist
```

### 9.3. Prohibited or restricted analytics

By default, normal consumers MUST NOT see:

```text
other consumers' data
raw source paths
internal review notes
hidden quality flags
global organization metrics without authorization
billing details beyond their own scope
security-sensitive operational detail
```

---

## 10. Source-of-Truth Hierarchy

Analytics precedence must be explicit:

### 10.1. Canonical hierarchy

1. Canonical database records and immutable events
2. Generated reports with recorded inputs
3. Derived materialized views
4. Dashboards built from reports/views
5. Screenshots/export files derived from dashboards

### 10.2. Forbidden precedence inversion

The system MUST NOT treat:

```text
dashboard screenshot as source truth;
manual spreadsheet as canonical report;
payment provider portal as canonical entitlement usage source;
Telegram chat history as canonical delivery ledger;
generated README as manually editable truth.
```

---

## 11. Analytics Event and Report Model

### 11.1. Canonical analytics inputs

Analytics may derive from:

```text
source registry records
file inventory outputs
import manifests
import batches and validation results
item status changes
taxonomy tables
deliveries
attempts
usage events
issue reports
audit logs
job runs
health/readiness signals
```

### 11.2. Canonical analytics outputs

Outputs may include:

```text
status distribution report
coverage report
delivery report
attempt correctness report
quota usage report
quality review queue report
operations health report
demo evidence report
dashboard projection
```

### 11.3. Reproducibility metadata

Every analytics output SHOULD record:

```text
report_id
report_type
generated_at
snapshot_time
scope_type
scope_id
parameters_json
source_inputs_json
generation_tool_or_job
status
limitations
```

---

## 12. Corpus Analytics

### 12.1. Purpose

Corpus analytics answers:

```text
What exists in the governed corpus?
What statuses exist?
How is content distributed?
What changed between snapshots?
```

### 12.2. Required corpus metrics

| Metric | Meaning |
|---|---|
| `active_source_files` | Count of active source bank files in current source snapshot |
| `active_rows` | Count of active source rows/items in source snapshot |
| `items_by_status` | Count by `draft/imported/normalized/needs_review/approved/published/monitored/retired/blocked` |
| `items_by_level` | Count by `A1–C2` |
| `items_by_theme` | Count by primary theme |
| `items_by_objective` | Count by objective |
| `items_by_pattern` | Count by pattern |
| `status_transition_counts` | Counts of lifecycle changes over period |
| `new_sources_onboarded` | Count of newly registered sources |

### 12.3. Corpus analytics invariant

Corpus analytics MUST distinguish:

```text
source existence
canonical normalization
production eligibility
actual published delivery
```

---

## 13. Coverage Analytics

### 13.1. Coverage purpose

Coverage analytics exists to measure completeness and imbalance across:

```text
level × theme × objective × pattern
```

### 13.2. Required coverage outputs

```text
coverage matrix
coverage gap list
coverage by publishable status
coverage delta after onboarding/import
coverage report for demo evidence
```

### 13.3. Coverage rule

Coverage reports MUST:

```text
count draft items separately from approved/published;
show missing cells explicitly where feasible;
preserve snapshot identity;
be reproducible from source or canonical state.
```

---

## 14. Delivery Analytics

### 14.1. Delivery purpose

Delivery analytics answers:

```text
What was delivered?
To whom?
Through which consumer/channel?
With what outcome?
How often?
How reliably?
```

### 14.2. Required delivery event fields

Delivery analytics MUST preserve at least:

```text
delivery_id
consumer_id
consumer_type
channel_or_endpoint
quiz_item_id
quiz_item_version_id where applicable
status_at_delivery
delivery_timestamp
delivery_outcome
repeat_policy_result
idempotency_key if used
```

### 14.3. Delivery metrics

| Metric | Meaning |
|---|---|
| `delivery_count` | Number of successful deliveries |
| `delivery_failed_count` | Number of failed deliveries |
| `delivery_success_rate` | Successful deliveries / attempted deliveries |
| `deliveries_by_consumer_type` | Breakdown by Telegram/API/web/etc. |
| `deliveries_by_level_theme` | Delivered content mix |
| `repeat_violations` | Actual or attempted repeat-policy violations |
| `delivery_latency` | Time from request/schedule to delivery result when measurable |

### 14.4. Delivery analytics invariant

Delivery analytics MUST NOT count a selection attempt, scheduling reservation or failed send as successful delivery unless policy explicitly defines a separate metric.

---

## 15. Attempt Analytics

### 15.1. Attempt purpose

Attempt analytics exists only where consumer flow supports attempts. It answers:

```text
How many attempts were recorded?
What correctness and timing patterns exist?
Which item versions are producing confusing outcomes?
Which consumers/users are active within authorization scope?
```

### 15.2. Required attempt fields

Attempt analytics SHOULD preserve:

```text
attempt_id
delivery_id when available
consumer_id
user_id or pseudonymous actor_id when allowed
quiz_item_id
quiz_item_version_id
selected_option_ids or normalized answer
correctness
response_timestamp
response_time_ms or equivalent if available
attempt_channel
```

### 15.3. Attempt metrics

| Metric | Meaning |
|---|---|
| `attempt_count` | Number of recorded attempts |
| `correctness_rate` | Correct attempts / evaluable attempts |
| `median_response_time` | Median response time where captured |
| `attempts_per_item` | Distribution of attempts by item |
| `attempts_per_consumer` | Usage pattern by consumer scope |
| `attempts_by_level_theme` | Learning interaction distribution |

### 15.4. Attempt caution rule

Correctness and response-time analytics MUST be clearly marked as:

```text
not available
insufficient sample
consumer-limited
pilot-only
```

when evidence is incomplete.

---

## 16. Billing and Usage Analytics

### 16.1. Billing/usage purpose

Analytics must explain monetized or protected usage without confusing payment status, entitlement state and quota consumption.

### 16.2. Required billing/usage metrics

| Metric | Meaning |
|---|---|
| `usage_events_total` | Count of usage events by event type/status |
| `quota_usage_by_plan` | Consumption by plan and quota policy |
| `quota_denials` | Denials caused by quota limits |
| `entitlement_denials` | Denials caused by missing/expired entitlement |
| `usage_by_consumer_type` | API/Telegram/school/etc. consumption |
| `feature_utilization` | Which paid/protected features are actually used |
| `billing_event_backlog` | Unresolved provider/internal billing events |

### 16.3. Billing analytics invariant

Billing analytics MUST use internal:

```text
entitlements
quota windows
usage events
billing events
```

and MUST NOT infer access solely from provider state.

---

## 17. Quality Analytics

### 17.1. Quality purpose

Quality analytics supports targeted review, not popularity-driven governance.

### 17.2. Required quality signals

```text
item issue reports
wrong-answer reports
abnormal correctness rate
abnormal response-time patterns
high failure clusters by source/theme/pattern
status changes to monitored/needs_review/blocked
source/import cohorts associated with anomalies
```

### 17.3. Quality metrics

| Metric | Meaning |
|---|---|
| `report_count_per_item` | Number of issue reports by item |
| `items_in_monitored` | Published items under observation |
| `items_needing_review` | Items routed to review queue |
| `quality_flag_rate` | Share of items or deliveries triggering quality signals |
| `anomaly_clusters` | Grouped suspicious items by source/theme/pattern/version |

### 17.4. Quality governance rule

Analytics may influence:

```text
review priority
selection ranking
monitoring attention
source health investigation
```

but MUST NOT auto-clear blocked items or auto-publish draft items.

---

## 18. Operational Analytics

### 18.1. Operational purpose

Operational analytics measures whether the analytics layer and its dependent flows are healthy enough for launch and support.

### 18.2. Required operational metrics

| Metric | Meaning |
|---|---|
| `report_generation_success_rate` | Successful report jobs / all report jobs |
| `report_generation_failures` | Count by report type/cause |
| `report_freshness_lag` | Current age vs expected freshness |
| `telegram_delivery_success_rate` | Telegram send reliability |
| `api_usage_rate` | Request and protected-delivery usage levels |
| `ops_incident_count` | Analytics-relevant incidents by severity |
| `audit_event_volume` | Rate of critical admin/billing/security actions |

### 18.3. Operational analytics invariant

Operational dashboards MUST show failures and stale data explicitly. Quiet failure is forbidden.

---

## 19. Security and Authorization Analytics

### 19.1. Purpose

Security-related analytics exists to support threat visibility, not public curiosity.

### 19.2. Allowed security analytics examples

```text
authorization denials by endpoint family
cross-consumer access attempts blocked
admin override volume
report export volume
billing webhook failures
token/key revocation events
```

### 19.3. Restricted security analytics rule

Security analytics MUST be role-gated and MUST NOT expose secrets, raw tokens, PII beyond justified scope or attack-replay-enabling detail.

---

## 20. Stanford Demo Analytics

### 20.1. Demo purpose

Stanford-style demo analytics must prove system coherence, not inflate numbers.

### 20.2. Minimum demo analytics evidence

For a credible demo, the project SHOULD be able to show:

```text
corpus snapshot by status/level/theme
coverage matrix or coverage summary
delivery log excerpt
usage/quota evidence
quality or issue-report signal
analytics report metadata with snapshot time
clear separation of demo/test vs production-like scope
```

### 20.3. Demo honesty rule

Demo MUST NOT:

```text
show hardcoded dashboard numbers as live analytics;
hide snapshot date;
mix unrelated consumers into one scoped report without explanation;
claim learner progress analytics if only delivery counts exist;
claim production reliability if only local dry-run evidence exists.
```

---

## 21. Analytics Dimensions and Segmentation

Analytics projections SHOULD support segmentation by:

```text
status
level
theme
objective
pattern
source_id
import_batch
consumer_type
consumer_id
organization_id
channel
time window
plan
feature
environment
demo/test/production-like flag
```

Segmentation MUST respect authorization scope.

---

## 22. Core Metric Catalog

### 22.1. Minimum metric catalog by domain

| Domain | Minimum metrics |
|---|---|
| Corpus | active items, items by status, items by level/theme/objective/pattern |
| Coverage | populated cells, missing cells, publishable coverage, coverage delta |
| Delivery | delivery count, success/failure, repeat result, consumer breakdown |
| Attempts | attempt count, correctness rate, response time, item/consumer distribution |
| Billing/Usage | quota usage, denials, feature utilization, unresolved billing events |
| Quality | report count, monitored items, review queue volume, anomaly clusters |
| Operations | report freshness, report failures, Telegram reliability, analytics job health |
| Demo | snapshot timestamp, evidence artifact count, demo-safe scoped reports |

### 22.2. Metric definition rule

Every metric SHOULD define:

```text
name
domain
source facts
formula
scope
freshness expectation
privacy classification
owner
```

---

## 23. Report Catalog

### 23.1. Required report types

The analytics model MUST support at least:

```text
corpus snapshot report
status distribution report
coverage report
source onboarding/change report
delivery report
attempt/correctness report
quota usage report
quality issue report
operations health report
demo evidence report
```

### 23.2. Required report metadata

Each report SHOULD include:

```text
report_id
report_type
scope
generated_at
snapshot_time
input artifacts or source query version
owner/job/tool
status
limitations
```

### 23.3. Generated report rule

Generated analytics reports are derived artifacts. Manual editing of them as truth is prohibited.

---

## 24. Data Freshness and Timeliness

### 24.1. Freshness expectations

| Report / metric family | MVP/Pilot expectation | Production target |
|---|---|---|
| Corpus snapshot | On demand / before demo | Scheduled or on corpus change |
| Coverage report | On import/release | Daily or on corpus change |
| Delivery report | On demand / daily | Near-real-time or scheduled |
| Attempt report | On demand / daily where attempts exist | Near-real-time or scheduled |
| Quota usage | On demand | Near-real-time for paid/protected flows |
| Operations health | Before launch/demo | Continuous or frequent polling |

### 24.2. Staleness rule

If a report is older than its declared freshness expectation, it MUST be marked stale or degraded.

---

## 25. Aggregation and Materialization Model

### 25.1. MVP style

MVP MAY use:

```text
database views
SQL aggregate queries
scheduled report jobs
generated Markdown/JSON reports
```

### 25.2. Future scale

Later phases MAY add:

```text
materialized views
analytics worker
warehouse
event stream
BI dashboard layer
difficulty calibration models
```

### 25.3. Materialization rule

Cached/materialized analytics MUST be:

```text
traceable to source facts
refreshable
scope-safe
invalidatable on major data change
```

---

## 26. Privacy and Data Minimization

### 26.1. Privacy principle

Analytics must reveal enough to make decisions, but not enough to violate privacy or authorization.

### 26.2. Privacy rules

1. Teachers may see their own classes/groups, not unrelated organizations.
2. API consumers may see only their own usage and authorized projections.
3. Personal learner analytics MUST remain limited until privacy/legal posture is explicit.
4. Billing data MUST NOT appear in normal analytics exports unless the scope explicitly requires it.
5. Demo analytics SHOULD prefer aggregate or synthetic-safe data where detailed personal data is unnecessary.

### 26.3. Restricted fields

Default analytics outputs SHOULD NOT expose:

```text
email addresses unless explicitly authorized
raw billing profile data
payment identifiers beyond need
secret metadata beyond safe labels
raw source file system paths
internal review notes
full admin audit payloads
```

---

## 27. Retention and Historical Analytics

### 27.1. Historical principle

Retired or blocked content may remain analytically queryable for history, but must not re-enter delivery by accident.

### 27.2. Retention expectations

| Data family | Retention posture |
|---|---|
| Generated reports | Retain enough for audit/demo/release evidence and supersession trace |
| Delivery events | Retain for repeat policy, analytics and dispute support |
| Attempt events | Retain per privacy policy and learning-value justification |
| Usage/billing analytics | Retain for quota, support, disputes and plan review |
| Demo/test analytics data | Mark and prune/reset regularly |

### 27.3. Historical query rule

Historical analytics MUST preserve:

```text
status context
snapshot identity
consumer scope
environment/demo flag where relevant
```

---

## 28. Analytics API and Admin Surface

### 28.1. Candidate analytics API surface

Potential API endpoints:

```text
GET /v1/analytics/summary
GET /v1/analytics/corpus
GET /v1/analytics/coverage
GET /v1/analytics/deliveries
GET /v1/analytics/attempts
GET /v1/analytics/usage
GET /v1/analytics/quality
GET /v1/analytics/operations
```

### 28.2. Candidate admin analytics surface

Potential admin/report endpoints:

```text
GET /v1/admin/analytics/reports
GET /v1/admin/analytics/reports/{report_id}
POST /v1/admin/analytics/reports/generate
GET /v1/admin/analytics/quality
GET /v1/admin/analytics/operations
GET /v1/admin/analytics/delivery-failures
GET /v1/admin/analytics/quota-usage
```

### 28.3. API rule

Analytics endpoints MUST:

```text
use role-appropriate projections;
enforce object-level authorization;
communicate freshness and scope;
avoid leaking internal-only fields;
document limitations in contract and/or report metadata.
```

---

## 29. Analytics Data Model Seeds

### 29.1. Core entities

Recommended entities/tables/views:

```text
analytics_reports
generated_reports
coverage_cells
delivery_events or deliveries
attempts
usage_events
issue_reports
analytics_metric_snapshots
report_jobs
report_artifacts
```

### 29.2. Example `analytics_reports` fields

```text
analytics_report_id
report_type
scope_type
scope_id
parameters_json
snapshot_time
status
result_summary_json
artifact_path
generated_by_job
created_at
completed_at
```

### 29.3. Example `analytics_metric_snapshots` fields

```text
metric_snapshot_id
metric_name
metric_domain
scope_type
scope_id
time_window_start
time_window_end
metric_value_json
source_reference_json
generated_at
```

### 29.4. Data model rule

Analytics storage MUST preserve reproducibility and scope metadata, not just final numbers.

---

## 30. Analytics Integration Rules

### 30.1. Import and corpus integration

Analytics must integrate with:

```text
source onboarding
file inventory
import manifest
validation/import reports
status workflow
coverage reports
```

### 30.2. Selection and delivery integration

Analytics must integrate with:

```text
selection engine decisions
delivery logs
repeat-policy outcomes
consumer/channel metadata
Telegram/API adapters
```

### 30.3. Attempts integration

Where supported, attempts must link to:

```text
delivered item context
user/actor context within privacy limits
correctness evaluation
timing metadata
```

### 30.4. Billing integration

Billing analytics must integrate with:

```text
entitlements
quota policies
usage events
billing events
plan/feature catalog
```

### 30.5. Operations integration

Operational analytics must integrate with:

```text
report jobs
health/readiness status
incident data
Telegram delivery failures
release/launch evidence
```

---

## 31. Analytics Calculation Rules and Anti-Patterns

### 31.1. Calculation rules

1. Metrics SHOULD be deterministic within a fixed snapshot and scope.
2. Aggregates SHOULD document excluded populations or missing data.
3. Attempt-based quality signals SHOULD define minimum sample thresholds before interpretation.
4. Time-windowed metrics SHOULD define timezone, window boundary and reset logic.
5. Demo and test records SHOULD be labeled so they can be excluded or isolated.

### 31.2. Anti-patterns

Forbidden or strongly discouraged analytics behavior:

```text
mixing draft and published counts without labeling;
using screenshot-only evidence;
using current live counters to explain historical release decisions without snapshot archive;
reporting “engagement” without defining event source;
treating denied quota events as successful usage;
combining unrelated organizations into one visible chart for a normal teacher;
silently dropping failed report jobs from dashboards.
```

---

## 32. Analytics QA and Test Strategy

### 32.1. Quality goal

Analytics must be consistent, scoped, reproducible and safe.

### 32.2. Test catalog

| Test ID | Test | Priority | Phase | Method |
|---|---|---:|---|---|
| AN-TC-001 | Corpus report matches canonical corpus status/level/theme counts. | P0 | MVP | A |
| AN-TC-002 | Coverage report distinguishes draft from publishable items. | P0 | MVP | A |
| AN-TC-003 | Delivery report count matches delivery records. | P0 | MVP/Pilot | T/A |
| AN-TC-004 | Delivery analytics preserve consumer/channel scope. | P0 | MVP/Pilot | T |
| AN-TC-005 | Attempt analytics link to item/version context when available. | P1 | Pilot | T |
| AN-TC-006 | Consumer-scoped analytics cannot expose another consumer's data. | P0 | MVP/Pilot | T |
| AN-TC-007 | Usage/quota analytics match usage_events and denial records. | P1 | Pilot | T/A |
| AN-TC-008 | Quality issue reports appear in analytics/admin review path. | P1 | Beta | T/D |
| AN-TC-009 | Every generated analytics report contains snapshot/freshness metadata. | P0 | MVP | A/I |
| AN-TC-010 | Demo analytics are clearly labeled as demo/test or scoped aggregate evidence. | P1 | Demo | I/R |
| AN-TC-011 | Stale report status is visible when freshness target is missed. | P1 | Pilot | T/A |
| AN-TC-012 | Telegram delivery analytics distinguish failed vs successful send outcomes. | P1 | Pilot | T/A |

---

## 33. Analytics Launch Gates

### 33.1. MVP analytics gate

MVP analytics is accepted when:

```text
basic corpus/status/coverage report exists;
delivery events are recorded;
analytics reports have metadata and reproducible inputs;
authorization blocks cross-consumer analytics access;
demo can show safe basic analytics evidence;
```

### 33.2. Closed pilot analytics gate

Pilot analytics is accepted when:

```text
delivery report exists for pilot consumer(s);
attempt analytics exists where flow supports it;
quota/usage analytics exists for protected flows;
repeat-related reporting exists;
report freshness and failures are visible operationally;
```

### 33.3. Public beta analytics gate

Beta analytics is accepted when:

```text
quality issue reporting analytics exists;
consumer-facing scoped analytics projections are stable;
privacy review covers beta analytics exposures;
operations dashboards and alerts cover analytics/report failures;
```

### 33.4. Production analytics gate

Production analytics is accepted when:

```text
analytics lineage and retention are documented;
report jobs are monitored;
restore/recovery covers analytics-critical records;
billing/usage analytics supports support and dispute workflows;
Stanford/demo artifacts can be generated honestly from system evidence;
```

---

## 34. Analytics Requirements

| ID | Requirement | Priority | Verification |
|---|---|---:|---|
| AN-REQ-001 | The system SHALL support corpus analytics by status, level and theme. | P0 | A |
| AN-REQ-002 | The system SHALL support coverage reporting by canonical taxonomy dimensions. | P0 | A |
| AN-REQ-003 | The system SHALL record and report delivery events by consumer and outcome. | P0 | T/A |
| AN-REQ-004 | The system SHALL prevent analytics exposure across unauthorized consumer boundaries. | P0 | T |
| AN-REQ-005 | The system SHALL attach snapshot/freshness metadata to generated analytics reports. | P0 | A/I |
| AN-REQ-006 | The system SHOULD support attempt analytics where attempt capture exists. | P1 | T/A |
| AN-REQ-007 | The system SHOULD support quota/usage analytics for protected delivery flows. | P1 | T/A |
| AN-REQ-008 | The system SHOULD support item quality analytics based on issue reports and observed signals. | P1 | A/T |
| AN-REQ-009 | The system SHOULD surface analytics/report generation failures operationally. | P1 | O/T |
| AN-REQ-010 | The system SHALL support basic demo-safe analytics evidence for Stanford-style presentation. | P1 | D/A |
| AN-REQ-011 | The system MAY support advanced correctness/difficulty analytics after sufficient attempt volume exists. | P3 | A |
| AN-REQ-012 | The system MAY support warehouse/BI extraction after canonical analytics lineage is stable. | P3 | D |

---

## 35. Traceability Matrix

| Analytics area | Primary traceability |
|---|---|
| Corpus analytics | `CONSTITUTION.md` section 24, SRS-AN-005, UC-012 |
| Delivery analytics | SRS-AN-001, SRS-AN-002, UC-005, UC-029 |
| Attempt analytics | SRS-AN-003, SRS-AN-004, UC-006, UC-029 |
| Quality analytics | Constitution quality metrics, SRS-AN-008, UC-009, UC-019 |
| Billing/usage analytics | `11_billing_model.md`, SRS-AN-002, SRS-BILL, UC-008, UC-029 |
| Operations analytics | `10_operations.md` sections 14 and 28, NFR-OPS traces |
| Demo analytics | Constitution Stanford-ready section, SRS-AN-011, UC-015 |

---

## 36. Analytics Risk Register

| Risk ID | Risk | Severity | Mitigation |
|---|---|---:|---|
| AN-RISK-001 | Analytics counts draft and publishable items together and misleads launch decisions. | High | Separate status-aware metrics and QA checks |
| AN-RISK-002 | Cross-consumer analytics leakage exposes private data. | Critical | Object-level authorization and scoped projections |
| AN-RISK-003 | Demo uses stale or manually edited report. | High | Generated metadata, artifact traceability, demo checklist |
| AN-RISK-004 | Delivery counts differ from delivery log source. | High | Reconciliation tests and source-of-truth hierarchy |
| AN-RISK-005 | Quota analytics treat denied requests as successful usage. | High | Separate event statuses and billing QA |
| AN-RISK-006 | Attempt analytics overclaims learner insight from too little data. | Medium | Sample thresholds and “insufficient data” states |
| AN-RISK-007 | Report jobs fail silently. | High | Ops dashboards, alerts, failed status visibility |
| AN-RISK-008 | Quality analytics overrides governance decisions automatically. | High | Status workflow remains authoritative |
| AN-RISK-009 | Demo/test traffic pollutes production-like analytics. | Medium | Environment/test flags and report filters |
| AN-RISK-010 | Historical analytics loses snapshot identity. | Medium | Snapshot metadata and report lineage |

---

## 37. Stanford-Style Analytics Demo

### 37.1. Demo flow

Recommended analytics demo flow:

1. Show corpus snapshot report with status/level/theme breakdown.
2. Show coverage report or matrix with explicit snapshot timestamp.
3. Show one delivery report scoped to demo consumer or safe aggregate.
4. Show one usage/quota report if protected flows are in scope.
5. Show one quality signal or review-oriented report.
6. Show report metadata: generated_at, snapshot_time, limitations.
7. Explain what is implemented now vs planned later.

### 37.2. Demo evidence artifacts

Potential demo evidence:

```text
corpus snapshot report
coverage report
delivery log excerpt
quota usage excerpt
quality issue summary
operations/readiness summary for analytics jobs
```

### 37.3. Demo failure condition

If analytics evidence cannot be tied back to system records, the demo claim should be withdrawn or restated more narrowly.

---

## 38. Analytics Acceptance Criteria

AN-AC-001  This document defines corpus, delivery, attempt, billing/usage, quality and operational analytics domains.  
AN-AC-002  It defines analytics source-of-truth hierarchy and reproducibility rules.  
AN-AC-003  It defines privacy and authorization boundaries for analytics access.  
AN-AC-004  It defines report metadata, freshness and staleness expectations.  
AN-AC-005  It defines candidate analytics API/admin surfaces.  
AN-AC-006  It defines analytics QA expectations and launch gates.  
AN-AC-007  It defines Stanford-style demo evidence for analytics.  
AN-AC-008  It maps analytics expectations to Constitution, SRS, use cases, architecture, operations and billing.  
AN-AC-009  It avoids claiming implementation details that are not yet committed in the repository.  

---

## 39. Open Analytics Questions

OQ-AN-001  Which dashboard/report tool launches first: generated Markdown/JSON only, admin UI, or BI tool?  
OQ-AN-002  Which analytics views are exposed externally in Pilot vs kept admin-only?  
OQ-AN-003  What minimum attempt volume is required before correctness/difficulty analytics is interpreted as meaningful?  
OQ-AN-004  What exact freshness target applies to each production analytics surface?  
OQ-AN-005  How much per-user learner analytics is allowed under the eventual privacy model?  
OQ-AN-006  Which export formats are mandatory first: JSON, CSV, dashboard-only, PDF?  
OQ-AN-007  Will Telegram delivery analytics be near-real-time or batch-generated first?  
OQ-AN-008  Which metrics are demo-only, pilot-only and production-critical?  
OQ-AN-009  Will analytics lineage remain in the primary PostgreSQL database or move partially to a warehouse later?  
OQ-AN-010  Which anomaly thresholds should route item to `monitored` vs `needs_review`?  

---

## 40. Implementation Roadmap

### 40.1. Phase 1 — MVP analytics foundation

```text
Define report metadata model.
Generate corpus/status/coverage reports.
Record delivery events.
Define demo-safe analytics artifacts.
Add authorization checks for analytics projections.
```

### 40.2. Phase 2 — Pilot delivery and usage analytics

```text
Add delivery report by consumer/channel.
Add basic usage/quota analytics for protected flows.
Add stale/failure visibility for report jobs.
Add safe analytics admin endpoints.
```

### 40.3. Phase 3 — Attempt and quality analytics

```text
Add attempt recording analytics where applicable.
Add correctness and response-time summaries.
Add issue-report and quality-signal analytics.
Add monitored/review queue reporting.
```

### 40.4. Phase 4 — Production-ready analytics operations

```text
Add monitored report jobs and freshness tracking.
Add retention and archive policy.
Add restore coverage for analytics-critical records.
Add organization/consumer scoped dashboards.
```

### 40.5. Phase 5 — Advanced analytics

```text
Difficulty calibration after sufficient data.
Warehouse/materialized view optimization.
Advanced classroom/organization analytics.
Improved demo/export package.
```

---

## 41. Reference Standards and Alignment

This document aligns with:

- `CONSTITUTION.md` sections on analytics purpose, item analytics, consumer analytics and Stanford-ready presentation
- `docs/02_requirements_srs.md` section 9.15 analytics and reporting requirements
- `docs/03_use_cases.md` UC-012 and UC-029
- `docs/04_domain_model.md` section 20 analytics and reporting model
- `docs/05_architecture.md` section 24 analytics and reporting architecture
- `docs/09_quality_assurance.md` section 34 analytics and reporting QA
- `docs/10_operations.md` section 28 analytics and reporting operations
- `docs/11_billing_model.md` section 34 billing analytics

---

## 42. Final Analytics Rule

API Quiz Bank is not analytics-ready because charts exist.

API Quiz Bank becomes analytics-ready when the system can prove:

```text
which facts were recorded,
which metrics were derived,
which scope and snapshot were used,
which privacy limits were enforced,
which limitations remain,
and which product, quality, billing, operations or demo decision the analytics can legitimately support.
```

No analytics output may be treated as product truth, billing evidence or Stanford-style proof unless lineage, scope, freshness and authorization are explicit.
