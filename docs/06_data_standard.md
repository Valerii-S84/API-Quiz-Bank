# API Quiz Bank — Data Standard

**Документ:** `docs/06_data_standard.md`  
**Назва проєкту:** API Quiz Bank  
**Внутрішня історична назва:** QuizBank / German QuizBank Platform  
**Версія:** 1.0.0  
**Статус:** foundational data standard; subordinate to `CONSTITUTION.md`; aligned with `00_vision.md`, `01_product_charter.md`, `02_requirements_srs.md`, `03_use_cases.md`, `04_domain_model.md`, `05_architecture.md`  
**Дата:** 2026-04-30  
**Мова:** українська з канонічними технічними термінами англійською  
**Власник:** project owner / authorized product maintainer  
**Керівні документи:** `CONSTITUTION.md`, `docs/00_vision.md`, `docs/01_product_charter.md`, `docs/02_requirements_srs.md`, `docs/03_use_cases.md`, `docs/04_domain_model.md`, `docs/05_architecture.md`  
**Наступні документи:** `07_api_standard.md`, `08_security_threat_model.md`, `09_quality_assurance.md`, `10_operations.md`, `11_billing_model.md`, `12_analytics_model.md`, `13_stanford_presentation_outline.md`

---

## 0. Executive Summary

`06_data_standard.md` визначає **канонічний стандарт даних API Quiz Bank**.

Цей документ встановлює, як raw quiz files, future source files, import manifests, parser profiles, normalized candidates, canonical quiz items, taxonomy, statuses, validation rules, hashes, projections, delivery records, attempts, entitlements and analytics data мають бути представлені, перевірені, змінені й використані.

Головна теза:

```text
API Quiz Bank is not production-ready because quiz files exist.
API Quiz Bank becomes production-ready when source files are governed,
quiz items are canonical, validation is machine-checkable,
statuses control publication, and every delivered item is traceable.
```

Поточний operational baseline, який підтримує цей standard:

```text
115 active bank files
30,974 active rows/items
top-level corpus format: CSV
CEFR levels: A1, A2, B1, B2, C1, C2
18 canonical themes
objective and pattern dimensions
all active items currently in draft operational status
local constitution check: violations=0 for 30,974 rows
```

Цей baseline є стартовим активом, а не верхньою межею. Data Standard закріплює правило:

```text
New quiz files are onboarded, not dropped.
```

Новий файл у майбутньому має пройти:

```text
source intake
  → stable source_id
  → checksum
  → file_inventory.csv / source registry
  → import_manifest.yml
  → parser_profile
  → dry-run import
  → normalized_quiz_candidate
  → canonical schema validation
  → duplicate/conflict classification
  → import_batch
  → quiz_item + quiz_item_version + quiz_option
  → status workflow
  → approved/published production delivery
  → generated reports
```

Цей документ НЕ проводить повторний педагогічний аудит усіх перевірених вікторин. Його focus — **operational data readiness**:

```text
source traceability
canonical schema
metadata completeness
status eligibility
validation rules
Telegram/API compatibility
future file onboarding
schema evolution
generated reports
testable data gates
```

---

## 1. Role of This Document

### 1.1. Purpose

`06_data_standard.md` відповідає на питання:

```text
Які дані є canonical?
Які поля обовʼязкові для production?
Як raw CSV стає canonical quiz item?
Як додавати нові файли без хаосу?
Які enum values дозволені?
Як рахувати source checksum і content hash?
Які validation rules блокують import, approval, publication or delivery?
Які JSON/YAML/CSV artifacts мають існувати?
Як відрізняється internal canonical item від API/Telegram projections?
Як schema versioning and change control працюють у product workflow?
Що має бути показано у Stanford-style demo як доказ data maturity?
```

### 1.2. Place in documentation hierarchy

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
data/schemas/*.schema.json
data/manifests/*.yml
data/taxonomy/*.yml
database/migrations/*
services / libs / tests / reports
```

### 1.3. What this document does

This document:

- defines canonical data artifacts;
- defines serialization and encoding rules;
- defines identifiers and naming conventions;
- defines source inventory and manifest standards;
- defines parser profile and import report standards;
- defines canonical quiz item field standard;
- defines statuses, source states, enum values and compatibility flags;
- defines validation rule catalog;
- defines checksum and hash rules;
- defines taxonomy and coverage rules;
- defines projection rules for API, Telegram, Admin, Analytics and Billing;
- defines generated report requirements;
- defines test and launch gates for data readiness.

### 1.4. What this document does not do

This document does not:

- replace the Software Requirements Specification;
- replace database migrations;
- replace OpenAPI contract;
- replace security threat model;
- replace operations runbook;
- define a polished UI;
- re-audit every verified quiz answer;
- permit direct public delivery from CSV.

---

## 2. Stanford-Style Data Discipline

For this project, “Stanford-style” means engineering discipline, not a marketing label.

Data must be:

```text
traceable
validated
versioned
testable
explainable
reproducible
auditable
operable
presentation-ready
```

A data claim is acceptable only when it can be backed by:

```text
source record
manifest entry
schema
validation result
import report
database record
status history
delivery log
generated report
test or demo evidence
```

### 2.1. Traceability chain

Every delivered production quiz item SHOULD be explainable through this chain:

```text
raw source file
  → source_id
  → source_checksum
  → import_manifest_entry
  → parser_profile
  → import_batch
  → normalized_quiz_candidate
  → validation_result
  → quiz_item
  → quiz_item_version
  → quiz_option
  → taxonomy
  → status
  → selection_request
  → delivery
  → attempt / analytics outcome
```

### 2.2. Non-negotiable data rule

```text
No source traceability, no production delivery.
No canonical schema, no API delivery.
No approved/published status, no normal consumer delivery.
No entitlement/quota check, no paid or limited delivery.
No delivery record, no scale claim.
```

---

## 3. Normative Language

The following terms are normative:

| Term | Meaning |
|---|---|
| **MUST / SHALL / ОБОВʼЯЗКОВО** | Required for compliance unless an explicit documented waiver exists. |
| **MUST NOT / SHALL NOT / ЗАБОРОНЕНО** | Prohibited behavior. |
| **SHOULD / РЕКОМЕНДОВАНО** | Expected default; exceptions need rationale. |
| **MAY / ДОЗВОЛЕНО** | Allowed option if it does not violate higher-level rules. |
| **P0** | Blocking for MVP/public delivery if applicable. |
| **P1** | Required for closed pilot/credible operation. |
| **P2** | Required for public beta/scale maturity. |
| **P3** | Future enhancement. |

---

## 4. Data Standard Scope

### 4.1. In scope

```text
raw source file rules
future source onboarding data
file inventory
import manifest
parser profiles
import batches
dry-run reports
normalized quiz candidates
canonical quiz item schema
quiz options and correct answer references
CEFR/theme/objective/pattern taxonomy
tags and secondary metadata
statuses and source states
checksum/content hash rules
duplicate/conflict data
consumer compatibility flags
API projections
Telegram projections
delivery/attempt data requirements
entitlement/quota data requirements
analytics/reporting data
data validation rules
data change control
generated reports
Stanford demo evidence data
```

### 4.2. Out of scope

```text
final SQL migrations
final OpenAPI endpoint contract
full security threat model
payment provider mapping details
full LMS integration schema
adaptive learning / IRT schema
public marketplace schema
AI-generated production content rules
full UI form specifications
```

---

## 5. Data Product Thesis

API Quiz Bank must treat data as a product.

A production quiz item is not merely a row. It is a governed object with:

```text
identity
source traceability
canonical content
answer structure
taxonomy
status
version
compatibility flags
quality signals
delivery history
access rules
analytics path
```

The core equation:

```text
raw file row + parser + manifest + validation + status + taxonomy + source traceability
  = canonical item candidate

canonical item candidate + approval/publication + delivery eligibility
  = production-deliverable quiz item
```

---

## 6. Authoritative Data Artifacts

The repository SHOULD include these artifacts.

```text
data/
  raw/
    README.md
    sources/
      src_000001/
      src_000002/
  manifests/
    file_inventory.csv
    import_manifest.yml
    parser_profiles.yml
    source_intake_template.yml
  taxonomy/
    cefr_levels.yml
    themes.yml
    objectives.yml
    patterns.yml
    tags.yml
    coverage_policy.yml
  schemas/
    quiz_item.schema.json
    quiz_item_public.schema.json
    normalized_quiz_candidate.schema.json
    import_manifest.schema.json
    parser_profile.schema.json
    source_file.schema.json
    validation_result.schema.json
    delivery.schema.json
    attempt.schema.json
    entitlement.schema.json
  normalized/
    quiz_items.sample.jsonl
    import_batch_samples/
  reports/
    inventory/
    import/
    validation/
    coverage/
    demo/
```

### 6.1. Artifact authority levels

| Artifact | Authority | Manual edit? | Notes |
|---|---|---:|---|
| `CONSTITUTION.md` | Governance law | Yes, controlled | Highest project rule. |
| `docs/06_data_standard.md` | Data policy | Yes, controlled | This document. |
| `data/schemas/*.schema.json` | Machine validation | Yes, controlled | Must match this document. |
| `data/manifests/import_manifest.yml` | Import configuration | Yes, controlled | PR/change control required. |
| `data/manifests/file_inventory.csv` | Generated or controlled inventory | Prefer generated | Should not become stale. |
| `data/taxonomy/*.yml` | Taxonomy truth | Yes, controlled | Change control required. |
| `data/normalized/*.jsonl` | Generated canonical samples | Generated | Not source of truth unless explicitly marked. |
| Database records | Operational source of truth after import | Through system only | Production truth after controlled import. |
| Raw files | Source assets | Immutable after registration | Not production delivery layer. |

---

## 7. Serialization and Encoding Standard

### 7.1. Formats

| Data type | Required / recommended format | Notes |
|---|---|---|
| Raw current corpus | CSV | Current top-level corpus format. |
| Source inventory | CSV or generated JSON | CSV for review, JSON for tooling. |
| Import manifest | YAML | Human-readable controlled config. |
| Parser profiles | YAML or JSON | YAML for maintainers; JSON Schema for validation. |
| Canonical samples | JSONL | One canonical object per line. |
| Canonical schema | JSON Schema Draft 2020-12 | Machine validation. |
| API contract | OpenAPI | Exact version decided in `07_api_standard.md`. |
| Reports | Markdown + JSON | Markdown for humans, JSON for tooling. |

### 7.2. Encoding

All project-controlled text files SHOULD use:

```text
UTF-8
```

CSV importers SHOULD accept:

```text
UTF-8
UTF-8 with BOM
```

Other encodings MAY be supported by parser profile only when explicitly declared.

### 7.3. Line endings

Repository-controlled text files SHOULD use LF line endings.

### 7.4. JSON and YAML rules

- JSON objects SHOULD use snake_case fields.
- JSON/YAML field names MUST be stable once public or used by tooling.
- Unknown fields MUST NOT be silently accepted in strict validation profiles.
- Controlled extensibility SHOULD use `metadata` or `x_*` extension fields when documented.
- Machine-readable schemas MUST reject fields that cause ambiguous semantics.

### 7.5. CSV rules

CSV source profile MUST define:

```text
delimiter
quote character
escape policy
encoding
header required/not required
column mapping
row locator strategy
empty row handling
comment row handling
formula-like cell handling
```

CSV importers MUST treat source cell contents as text unless parser profile explicitly converts them.

---

## 8. Naming Conventions

### 8.1. File naming

Repository artifacts SHOULD use lower_snake_case where possible:

```text
file_inventory.csv
import_manifest.yml
parser_profiles.yml
quiz_item.schema.json
normalized_quiz_candidate.schema.json
coverage_report.json
```

Raw historical filenames MAY preserve original names for traceability.

### 8.2. Field naming

Canonical JSON fields MUST use:

```text
snake_case
```

Examples:

```text
source_id
cefr_level
primary_theme_id
correct_option_ids
content_hash
import_batch_id
telegram_quiz_ready
```

### 8.3. ID prefixes

Recommended public/admin ID prefixes:

| Entity | Prefix | Example |
|---|---|---|
| Source file | `src_` | `src_000001` |
| Parser profile | `pp_` | `pp_csv_mcq_v1` |
| Import manifest entry | `ime_` | `ime_000001` |
| Import batch | `ib_` | `ib_20260430_0001` |
| Normalized candidate | `nqc_` | `nqc_01J...` |
| Quiz item | `qi_` | `qi_01J...` |
| Quiz item version | `qiv_` | `qiv_01J...` |
| Quiz option | `qopt_` | `qopt_01J...` |
| Consumer | `cons_` | `cons_01J...` |
| Consumer rule | `cr_` | `cr_01J...` |
| Entitlement | `ent_` | `ent_01J...` |
| Delivery | `deliv_` | `deliv_01J...` |
| Attempt | `att_` | `att_01J...` |
| Report | `rep_` | `rep_20260430_coverage` |
| Audit log | `aud_` | `aud_01J...` |

### 8.4. ID stability

- IDs MUST NOT be reused.
- `source_id` MUST survive filename changes.
- `quiz_item.public_id` MUST survive internal database migration.
- Human-readable slugs MAY change; stable IDs MUST NOT.

---

## 9. Time, Date and Version Standard

### 9.1. Timestamps

Timestamps MUST be stored in UTC.

Recommended serialized format:

```text
YYYY-MM-DDTHH:MM:SSZ
```

Example:

```text
2026-04-30T18:25:00Z
```

### 9.2. Dates

Business/reporting dates MAY use local timezone only if timezone is explicitly stored.

Example:

```yaml
report_date: 2026-04-30
timezone: Europe/Berlin
```

### 9.3. Schema versions

Canonical records MUST include schema version:

```json
"schema_version": "1.0.0"
```

Schema versions SHOULD follow semantic versioning:

| Change | Version effect |
|---|---|
| Add optional non-breaking field | Minor |
| Clarify validation wording without behavior change | Patch |
| Add required field | Major |
| Rename field | Major |
| Change enum semantics | Major |
| Tighten validation that rejects formerly valid production data | Major or controlled minor with migration |

---

## 10. Language and Text Standard

### 10.1. Language fields

Canonical multilingual text SHOULD use explicit language keys:

```json
{
  "stem": {
    "de": "Welche Antwort ist richtig?",
    "uk": null
  }
}
```

Minimum required production content:

```text
stem.de
options[].text.de
```

Optional support content:

```text
stem.uk
options[].text.uk
explanation.de
explanation.uk
```

### 10.2. Language code policy

Canonical keys for MVP:

```text
de  German
uk  Ukrainian
en  English, optional future/admin support
```

### 10.3. German text normalization

For validation and hashing, text normalization MUST:

```text
apply Unicode NFC
trim leading/trailing whitespace
collapse internal whitespace sequences to a single space, except where formatting is explicitly allowed
preserve German umlauts and ß
preserve display capitalization
preserve punctuation that affects meaning
remove invisible control characters unless explicitly allowed
```

For display, original approved text SHOULD be preserved except safe whitespace cleanup.

### 10.4. Empty and null values

- Missing optional field MAY be absent or `null` depending on schema.
- Required text fields MUST NOT be empty after normalization.
- Empty strings SHOULD NOT be used as “unknown”; use `null` or omit optional field.
- For CSV imports, empty cells MUST be interpreted by parser profile.

### 10.5. Text safety

Generated exports MUST protect against spreadsheet formula injection. If exporting user-visible CSV, values beginning with `=`, `+`, `-`, `@` SHOULD be escaped according to export policy.

---

## 11. Identifier Standard

### 11.1. Source ID

`source_id` identifies a source file independently of path and filename.

Required pattern:

```text
src_[0-9]{6}
```

Example:

```text
src_000001
```

Alternative ULID-based pattern MAY be adopted through change control.

### 11.2. Public quiz item ID

Public item IDs SHOULD be opaque.

Recommended pattern:

```text
qi_[A-Za-z0-9]+
```

The public item ID MUST NOT reveal:

```text
source filename
row number
internal sequential database ID if that creates scraping risk
```

### 11.3. Source locator

`source_locator` records where the item came from inside the source.

Recommended JSON shape:

```json
{
  "row_number": 128,
  "column_map": {
    "stem_de": "question",
    "correct_answer_raw": "correct"
  },
  "raw_row_hash": "sha256:..."
}
```

For non-CSV future files:

```json
{
  "sheet_name": "A2",
  "cell_range": "A128:F128",
  "raw_row_hash": "sha256:..."
}
```

### 11.4. Public vs internal IDs

Internal database IDs MAY be UUID, UUIDv7, ULID or bigint. This standard does not force the database primary key format.

Public/API IDs MUST remain stable regardless of database implementation.

---

## 12. Checksum and Hash Standard

### 12.1. Hash types

| Hash | Meaning | Input | Required |
|---|---|---|---:|
| `source_checksum_sha256` | Integrity hash of raw source file | Exact file bytes | Yes for registered/importable source |
| `raw_row_hash` | Hash of source row/block | Raw row/block canonical bytes | Recommended |
| `semantic_content_hash` | Dedupe hash of quiz content | Normalized stem/options/correct answer semantics | Yes for canonical candidate/item |
| `delivery_content_hash` | Hash of exact delivery projection | Stem/options order/explanation used for delivery | Recommended |
| `canonical_record_hash` | Hash of canonical content + selected metadata | Canonical item payload excluding volatile fields | Recommended |

### 12.2. Source checksum

`source_checksum_sha256` MUST be calculated over exact source file bytes.

Format:

```text
sha256:<64 lowercase hex characters>
```

Example:

```text
sha256:3b7a...
```

### 12.3. Semantic content hash

`semantic_content_hash` is used for duplicate detection.

Recommended v1 input:

```json
{
  "hash_algorithm_version": "semantic_content_hash_v1",
  "item_type": "single_choice",
  "stem_de": "<normalized stem>",
  "options_de": ["<normalized option text 1>", "<normalized option text 2>"],
  "correct_option_texts_de": ["<normalized correct option text>"],
  "language_mode": "de_only"
}
```

Rules:

- Exclude `source_id`.
- Exclude `status`.
- Exclude `approved_at`, `created_at`, `updated_at`.
- Exclude `delivery_id`.
- Exclude filename and path.
- Exclude taxonomy by default so same content with conflicting taxonomy can be detected.
- Preserve option correctness semantics.
- Either preserve option order or use a documented canonical sort. The project MUST choose and keep one behavior for v1.

### 12.4. Canonical record hash

`canonical_record_hash` MAY include:

```text
semantic content
cefr_level
primary_theme_id
objective_id
pattern_id
tags
item_type
language_mode
```

This is useful for versioning and migration comparison, but it is not a replacement for `semantic_content_hash`.

### 12.5. Hash immutability

If hashing algorithm changes, create new hash version fields or record `hash_algorithm_version`.

Do not silently reinterpret old hashes.

---

## 13. Source File Standard

### 13.1. Source file fields

Every source file record MUST support:

| Field | Type | Required | Notes |
|---|---|---:|---|
| `source_id` | string | yes | Stable source identity. |
| `source_slug` | string | recommended | Human-friendly stable-ish slug. |
| `filename` | string | yes | Current filename. |
| `original_filename` | string | yes | Preserved original filename. |
| `original_path` | string | yes | Original path at registration. |
| `current_path` | string | yes | Current repository/storage path. |
| `format` | enum | yes | `csv`, `xlsx`, `jsonl`, etc. |
| `encoding` | string/null | recommended | Example `utf-8`. |
| `checksum_sha256` | string | yes | Exact file checksum. |
| `size_bytes` | integer/null | recommended | File size. |
| `row_count_detected` | integer/null | recommended | Rows detected by tooling. |
| `expected_item_count` | integer/null | optional | From source intake. |
| `source_state` | enum | yes | See section 13.2. |
| `is_service_template` | boolean | yes | Distinguishes templates. |
| `registered_at` | datetime | yes | UTC. |
| `registered_by` | string/null | recommended | Actor/system. |
| `rights_status` | enum/null | recommended | Use rights status. |
| `notes` | string/null | optional | Operational notes. |

### 13.2. Source states

Allowed `source_state`:

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

### 13.3. Source state meaning

| State | Meaning | Can create production items? | Can deliver? |
|---|---|---:|---:|
| `candidate` | File proposed but not registered | No | No |
| `registered` | ID/checksum/inventory exists | No | No |
| `parser_pending` | Parser missing | No | No |
| `parser_assigned` | Parser assigned | Dry-run only | No |
| `dry_run_failed` | Dry-run failed | No | No |
| `dry_run_passed` | Dry-run passed | Controlled import possible | No |
| `imported` | Items imported to canonical/staging | Yes, but not delivery by default | No unless item approved/published |
| `active` | Source accepted into governed corpus | Yes | Only approved/published items |
| `archived` | Historical source | No new import by default | Existing items only if not retired |
| `rejected` | Source not accepted | No | No |
| `blocked` | Source blocked due to issue/risk | No | No |

### 13.4. Source invariants

- A source MUST have `source_id` before import.
- A source MUST have `checksum_sha256` before parser assignment.
- A source MUST have manifest entry before dry-run.
- A source MUST NOT be silently modified after registration.
- If file content changes, checksum changes and source versioning/re-registration policy applies.
- Rejected/blocked sources MUST NOT produce publishable items.
- Active source does not automatically mean all items are deliverable.

---

## 14. `file_inventory.csv` Standard

### 14.1. Purpose

`data/manifests/file_inventory.csv` is the human-auditable inventory of source files.

It may be generated by tooling, but the resulting data must be stable enough to support review, demo and import planning.

### 14.2. Minimum columns

```csv
source_id,source_slug,filename,original_path,current_path,format,encoding,checksum_sha256,size_bytes,row_count_detected,expected_item_count,source_state,is_service_template,parser_profile_id,manifest_entry_id,registered_at,last_seen_at,notes
```

### 14.3. Column rules

| Column | Required | Rule |
|---|---:|---|
| `source_id` | yes | Unique, stable. |
| `source_slug` | recommended | Lowercase slug; can change only by controlled update. |
| `filename` | yes | Current filename. |
| `original_path` | yes | Registration path. |
| `current_path` | yes | Current location. |
| `format` | yes | `csv` for current corpus. |
| `encoding` | recommended | `utf-8` if known. |
| `checksum_sha256` | yes | `sha256:<hex>`. |
| `size_bytes` | recommended | Non-negative integer. |
| `row_count_detected` | recommended | Non-negative integer. |
| `expected_item_count` | optional | Source-intake estimate. |
| `source_state` | yes | Valid source state enum. |
| `is_service_template` | yes | `true` or `false`. |
| `parser_profile_id` | conditional | Required before import. |
| `manifest_entry_id` | conditional | Required before import. |
| `registered_at` | yes | UTC timestamp. |
| `last_seen_at` | recommended | Inventory scan timestamp. |
| `notes` | optional | Human notes; no secrets. |

### 14.4. Generated inventory rule

If `file_inventory.csv` is generated, it MUST include a header or adjacent report stating:

```text
Generated by <tool>. Do not edit manually unless policy allows.
```

---

## 15. Source Intake Template Standard

### 15.1. Purpose

Every future source file SHOULD have intake metadata before it enters import workflow.

### 15.2. Template

```yaml
source_intake:
  proposed_source_name: "travel_a2_pack_may_2026"
  submitted_by: "content_admin"
  submitted_at: "2026-04-30T18:00:00Z"
  content_owner: "project_owner"
  intended_level_range: ["A2"]
  intended_theme_ids: ["T09"]
  expected_item_count: 100
  file_format: "csv"
  language_scope: ["de"]
  known_quality_status: "verified_by_owner"
  rights_to_use: "owned"
  known_parser_profile_id: null
  notes: "Candidate future source for onboarding demo."
```

### 15.3. Rights status values

Allowed `rights_status`:

```text
owned
licensed
partner_provided
internal_demo_only
unknown
rejected
```

No public/commercial delivery SHOULD use content with `rights_status=unknown`.

---

## 16. Import Manifest Standard

### 16.1. Purpose

`data/manifests/import_manifest.yml` maps source files to parser profiles, default taxonomy, import mode and onboarding state.

### 16.2. Manifest structure

```yaml
manifest_version: "1.0.0"
generated_at: null
updated_at: "2026-04-30T18:00:00Z"
sources:
  - manifest_entry_id: "ime_000001"
    source_id: "src_000001"
    source_state: "parser_assigned"
    parser_profile_id: "pp_csv_mcq_v1"
    import_mode: "dry_run"
    defaults:
      cefr_level: "A2"
      primary_theme_id: "T09"
      objective_id: "O09"
      pattern_id: "P01"
      item_type: "single_choice"
      language_mode: "de_only"
    column_mapping:
      sublevel: "cefr_level"
      question: "stem.de"
      option_a: "options[0].text.de"
      option_b: "options[1].text.de"
      option_c: "options[2].text.de"
      correct: "correct_answer_raw"
    validation_profile_id: "vp_quiz_item_mvp_v1"
    duplicate_policy: "flag"
    notes: "Current source imported through canonical parser."
```

### 16.3. Required manifest fields

| Field | Required | Notes |
|---|---:|---|
| `manifest_version` | yes | Schema of manifest file. |
| `sources[].manifest_entry_id` | yes | Stable manifest entry. |
| `sources[].source_id` | yes | Must exist in inventory. |
| `sources[].source_state` | yes | Must be valid source state. |
| `sources[].parser_profile_id` | conditional | Required before dry-run. |
| `sources[].import_mode` | yes | `dry_run`, `pilot`, `full`, `reimport`, `disabled`. |
| `sources[].defaults` | conditional | Required if source lacks those fields. |
| `sources[].column_mapping` | conditional | Required for parser if not implicit. |
| `sources[].validation_profile_id` | recommended | Which validation set applies. |
| `sources[].duplicate_policy` | recommended | `flag`, `block`, `allow_with_review`. |

### 16.4. Manifest invariants

- Manifest MUST reference sources by `source_id`, not filename only.
- Manifest MUST be version-controlled.
- Manifest changes that affect import behavior require change control.
- Manifest MUST NOT include secrets.
- Manifest MUST NOT silently coerce unknown taxonomy values.

---

## 17. Parser Profile Standard

### 17.1. Purpose

Parser profiles define how raw files become normalized quiz candidates.

### 17.2. Example

```yaml
parser_profiles:
  - parser_profile_id: "pp_csv_mcq_v1"
    name: "CSV multiple-choice parser v1"
    version: "1.0.0"
    supported_formats: ["csv"]
    encoding_policy:
      allowed: ["utf-8", "utf-8-sig"]
      default: "utf-8"
    csv:
      delimiter: ","
      quotechar: "\""
      header_required: true
    field_mapping:
      sublevel: "cefr_level"
      theme_id: "primary_theme_id"
      objective_id: "objective_id"
      pattern_id: "pattern_id"
      question: "stem.de"
      option_a: "options[0].text.de"
      option_b: "options[1].text.de"
      option_c: "options[2].text.de"
      option_d: "options[3].text.de"
      correct: "correct_answer_raw"
      status: "status"
    normalization_profile_id: "np_text_de_v1"
    validation_profile_id: "vp_quiz_item_mvp_v1"
    output_schema_id: "normalized_quiz_candidate.schema.json"
    test_fixtures:
      - "tests/fixtures/importers/csv_mcq_valid.csv"
      - "tests/fixtures/importers/csv_mcq_invalid.csv"
```

### 17.3. Parser profile required fields

```text
parser_profile_id
name
version
supported_formats
field_mapping
normalization_profile_id
validation_profile_id
output_schema_id
test_fixtures
```

### 17.4. Parser profile invariants

- Parser changes are data-impacting changes.
- Parser changes MUST have tests.
- Parser must preserve source locator.
- Parser must produce normalized candidates, not approved items.
- Parser must report errors with machine-readable reason codes.

---

## 18. Normalized Quiz Candidate Standard

### 18.1. Purpose

`normalized_quiz_candidate` is the object created after parsing but before production approval.

It is not yet a deliverable quiz item.

### 18.2. Required fields

| Field | Required | Notes |
|---|---:|---|
| `candidate_id` | yes | Stable within import batch. |
| `schema_version` | yes | Candidate schema version. |
| `import_batch_id` | yes | Origin import run. |
| `source_id` | yes | Origin source. |
| `source_locator` | recommended | Row/block. |
| `raw_row_hash` | recommended | Hash of raw row/block. |
| `normalized_payload` | yes | Candidate content. |
| `candidate_status` | yes | Candidate lifecycle status. |
| `validation_summary` | yes | Pass/warn/fail counts. |
| `duplicate_summary` | recommended | Duplicate/conflict result. |
| `semantic_content_hash` | yes | Dedupe hash. |
| `created_at` | yes | UTC. |

### 18.3. Candidate statuses

```text
parsed
normalized
schema_valid
schema_invalid
duplicate_candidate
conflict_candidate
ready_for_import
imported_as_item
rejected
blocked
```

### 18.4. Candidate invariants

- Candidate MUST NOT be delivered to normal consumers.
- Candidate MUST preserve `source_id`.
- Candidate SHOULD preserve raw row/block locator.
- Candidate MUST have validation result before import commit.
- Candidate with `schema_invalid` MUST NOT become approved item.

---

## 19. Import Batch and Import Report Standard

### 19.1. Import batch fields

```text
import_batch_id
source_id
manifest_entry_id
parser_profile_id
mode
status
started_at
completed_at
input_checksum_sha256
rows_seen
rows_parsed
candidates_created
candidates_valid
candidates_invalid
items_created
items_updated
items_skipped
validation_failures
duplicate_candidates
conflict_candidates
created_by
report_path
```

### 19.2. Import modes

```text
dry_run
canonical_write
production_write
reimport
rollback_test
```

### 19.3. Import batch statuses

```text
created
running
dry_run_completed
dry_run_failed
validation_failed
duplicate_review_required
ready_to_commit
committing
committed
partially_committed
failed
cancelled
rolled_back
superseded
```

### 19.4. Import report minimum content

Every import report MUST include:

```text
source_id
source checksum at import time
manifest_entry_id
parser_profile_id and version
import mode
row counts
accepted candidates
skipped rows
validation errors
duplicate candidates
conflict candidates
parser warnings
source traceability summary
sample normalized item if safe
recommendation: proceed / fix / reject / review
```

### 19.5. Dry-run rule

Dry-run import MUST NOT write approved/published production items.

---

## 20. Canonical Quiz Item Standard

### 20.1. Canonical item split

Canonical content is split into three conceptual layers:

```text
quiz_item          stable item identity, status, taxonomy, source traceability
quiz_item_version  versioned content snapshot
quiz_option        answer options belonging to a version
```

### 20.2. Minimum canonical item object

```json
{
  "schema_version": "1.0.0",
  "quiz_item_id": "qi_01J00000000000000000000000",
  "version_id": "qiv_01J00000000000000000000000",
  "status": "approved",
  "item_type": "single_choice",
  "language_mode": "de_only",
  "stem": {
    "de": "Welche Antwort ist richtig?",
    "uk": null
  },
  "options": [
    {
      "id": "qopt_01J00000000000000000000001",
      "position": 1,
      "text": {
        "de": "Option A",
        "uk": null
      },
      "is_correct": false
    },
    {
      "id": "qopt_01J00000000000000000000002",
      "position": 2,
      "text": {
        "de": "Option B",
        "uk": null
      },
      "is_correct": true
    }
  ],
  "correct_option_ids": [
    "qopt_01J00000000000000000000002"
  ],
  "explanation": {
    "de": "Kurze Erklärung.",
    "uk": null
  },
  "taxonomy": {
    "cefr_level": "A2",
    "primary_theme_id": "T09",
    "secondary_theme_ids": [],
    "objective_id": "O09",
    "pattern_id": "P01",
    "tags": ["artikel"]
  },
  "source": {
    "source_id": "src_000001",
    "import_batch_id": "ib_20260430_0001",
    "source_locator": {
      "row_number": 128,
      "raw_row_hash": "sha256:..."
    },
    "source_checksum_sha256": "sha256:...",
    "semantic_content_hash": "sha256:..."
  },
  "compatibility": {
    "api_delivery_ready": true,
    "telegram_quiz_ready": true,
    "teacher_pack_ready": true
  },
  "quality": {
    "validation_status": "passed",
    "review_required": false,
    "quality_flags": []
  },
  "timestamps": {
    "created_at": "2026-04-30T18:00:00Z",
    "updated_at": "2026-04-30T18:00:00Z",
    "approved_at": "2026-04-30T18:10:00Z",
    "published_at": null
  }
}
```

### 20.3. Required fields for any canonical item

```text
schema_version
quiz_item_id
version_id
status
item_type
language_mode
stem.de
options[]
correct_option_ids[]
source.source_id
source.import_batch_id
source.semantic_content_hash
timestamps.created_at
timestamps.updated_at
```

### 20.4. Required fields for approved/published items

```text
taxonomy.cefr_level
taxonomy.primary_theme_id
taxonomy.objective_id
taxonomy.pattern_id
quality.validation_status = passed
source.source_checksum_sha256
compatibility.api_delivery_ready = true
timestamps.approved_at
```

For Telegram delivery:

```text
compatibility.telegram_quiz_ready = true
```

### 20.5. `draft` meaning

`draft` means:

```text
not yet production-released through the platform workflow
```

It does not mean:

```text
incorrect
unusable
not verified as content
```

---

## 21. Field Catalog — Canonical Quiz Item

### 21.1. Identity fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `schema_version` | string | yes | Semantic schema version. |
| `quiz_item_id` | string | yes | Public or internal stable item ID. |
| `version_id` | string | yes | Current version ID. |
| `version_number` | integer | recommended | Monotonic per item. |

### 21.2. Content fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `stem.de` | string | yes | German question/stem. |
| `stem.uk` | string/null | optional | Ukrainian support. |
| `explanation.de` | string/null | optional | German explanation. |
| `explanation.uk` | string/null | optional | Ukrainian explanation. |
| `item_type` | enum | yes | `single_choice`, `multiple_choice`, etc. |
| `language_mode` | enum | yes | `de_only`, `de_uk_support`, etc. |

### 21.3. Options fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `options[].id` | string | yes | Stable option ID within version. |
| `options[].position` | integer | yes | 1-based canonical position. |
| `options[].text.de` | string | yes | German option text. |
| `options[].text.uk` | string/null | optional | Ukrainian support text. |
| `options[].is_correct` | boolean | yes | Correctness flag. |
| `correct_option_ids[]` | array | yes | References option IDs. |

### 21.4. Taxonomy fields

| Field | Type | Required for approved/published | Notes |
|---|---|---:|---|
| `taxonomy.cefr_level` | enum | yes | `A1`–`C2`. |
| `taxonomy.primary_theme_id` | enum | yes | `T01`–`T18`. |
| `taxonomy.secondary_theme_ids[]` | array | no | Additional themes. |
| `taxonomy.objective_id` | enum | yes | `Oxx`. |
| `taxonomy.pattern_id` | enum | yes | `Pxx`. |
| `taxonomy.tags[]` | array | recommended | Free/controlled tags. |

### 21.5. Source fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `source.source_id` | string | yes | Origin source. |
| `source.import_batch_id` | string | yes | Origin import batch. |
| `source.source_locator` | object/null | recommended | Row/block. |
| `source.source_checksum_sha256` | string | required for approved/published | Source file hash. |
| `source.raw_row_hash` | string/null | recommended | Row/block hash. |
| `source.semantic_content_hash` | string | yes | Dedupe hash. |
| `source.canonical_record_hash` | string/null | recommended | Version/change hash. |

### 21.6. Compatibility fields

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `compatibility.api_delivery_ready` | boolean | yes | Can be used by API delivery projection. |
| `compatibility.telegram_quiz_ready` | boolean | yes | Can be sent as Telegram quiz/poll. |
| `compatibility.teacher_pack_ready` | boolean | recommended | Can be used in teacher packs. |
| `compatibility.requires_explanation` | boolean | optional | Use where pedagogy requires explanation. |
| `compatibility.delivery_block_reason` | string/null | optional | Why not deliverable. |

### 21.7. Quality fields

```text
quality.validation_status
quality.review_required
quality.quality_flags[]
quality.duplicate_case_id
quality.issue_report_count
quality.last_reviewed_at
```

### 21.8. Timestamp fields

```text
timestamps.created_at
timestamps.updated_at
timestamps.imported_at
timestamps.approved_at
timestamps.published_at
timestamps.retired_at
timestamps.blocked_at
```

---

## 22. Option and Correct Answer Standard

### 22.1. Canonical position

Option position is 1-based in canonical data.

Example:

```json
{
  "position": 1
}
```

For Telegram projection, positions are converted to 0-based `correct_option_ids`.

### 22.2. Correct answer references

Correct answers MUST be represented by option IDs, not raw letters.

Bad canonical data:

```json
{"correct": "B"}
```

Good canonical data:

```json
{"correct_option_ids": ["qopt_01J00000000000000000000002"]}
```

Raw import MAY contain `A`, `B`, `C`, numeric position, text, or column name. Parser must resolve it into canonical option references.

### 22.3. Single-choice item

Rules:

```text
item_type = single_choice
exactly one option has is_correct=true
correct_option_ids length = 1
```

### 22.4. Multiple-choice item

Rules:

```text
item_type = multiple_choice
one or more options have is_correct=true
correct_option_ids length >= 1
consumer compatibility must confirm target supports multiple correct answers
```

### 22.5. Option validation

- Publishable item MUST have at least 2 options.
- Option IDs MUST be unique within item version.
- Positions MUST be unique within item version.
- Correct option IDs MUST reference existing options in the same version.
- Option display text MUST NOT be empty after normalization.
- Duplicate option text within same item SHOULD be flagged.

---

## 23. Item Type Standard

### 23.1. MVP item types

```text
single_choice
multiple_choice
```

### 23.2. Future item types

```text
gap_fill
matching
ordering
short_answer
cloze
translation_prompt
dialogue_reply
```

### 23.3. Item type delivery rule

An item type may exist in canonical storage before every consumer supports it.

But it MUST NOT be delivered to a consumer unless that consumer projection supports it.

Example:

```text
gap_fill may be valid for admin/database,
but not Telegram quiz delivery until Telegram adapter supports a safe projection.
```

---

## 24. Status Standard

### 24.1. Item statuses

Allowed item statuses:

```text
draft
imported
normalized
needs_review
approved
published
monitored
retired
blocked
```

### 24.2. Status meaning

| Status | Meaning | Normal delivery allowed? |
|---|---|---:|
| `draft` | Not production-released | No |
| `imported` | Imported from source | No |
| `normalized` | Parsed and normalized | No |
| `needs_review` | Requires review | No |
| `approved` | Eligible for controlled delivery | Yes |
| `published` | Actively public/production released | Yes |
| `monitored` | Live but under special observation | No for normal delivery by default |
| `retired` | No future delivery | No |
| `blocked` | Hard stop | No |

### 24.3. Delivery-allowed statuses

Normal delivery allowed:

```text
approved
published
```

`monitored` MUST NOT be treated as normal-delivery eligible unless a future change-control decision updates the delivery policy and related tests.

### 24.4. Status transition rules

Allowed default transitions:

```text
draft → imported
imported → normalized
normalized → needs_review
normalized → approved
needs_review → approved
approved → published
approved → retired
published → monitored
published → retired
published → blocked
monitored → published
monitored → retired
any non-final status → blocked
```

### 24.5. Status audit

Every status change MUST record:

```text
quiz_item_id
previous_status
new_status
actor
timestamp
reason_code
reason_note
```

---

## 25. Taxonomy Standard

### 25.1. Canonical CEFR levels

Allowed `cefr_level` values:

```text
A1
A2
B1
B2
C1
C2
```

No approved/published item may use another value.

### 25.2. Compatibility note: `sublevel`

Current active CSV field `sublevel` is a compatibility field name.

Canonical interpretation:

```text
sublevel → cefr_level
```

Allowed values remain:

```text
A1, A2, B1, B2, C1, C2
```

The platform MUST NOT create a separate canonical `sublevel` dimension unless a future change control decision defines one.

### 25.3. Themes

The current corpus uses 18 canonical themes.

Allowed theme IDs:

```text
T01
T02
T03
T04
T05
T06
T07
T08
T09
T10
T11
T12
T13
T14
T15
T16
T17
T18
```

Current canonical German theme family titles:

| theme_id | title_de |
|---|---|
| T01 | Person / Identität / Familie |
| T02 | Alltag / Zeit / Organisation |
| T03 | Wohnen / Haushalt / Verträge |
| T04 | Einkaufen / Geld / Konsum |
| T05 | Essen / Gesundheit / Pflege |
| T06 | Arbeit / Beruf / Karriere |
| T07 | Schule / Bildung / Weiterbildung |
| T08 | Verkehr / Reise / Orientierung |
| T09 | Kommunikation / Telefon / Nachricht / E-Mail |
| T10 | Termine / Formulare / Behörden / Recht |
| T11 | Freizeit / Kultur / Service / soziale Kontakte |
| T12 | Medien / Digitales / Nachrichten |
| T13 | Gesellschaft / Integration / Werte |
| T14 | Umwelt / Nachhaltigkeit / Alltagssysteme |
| T15 | Wirtschaft / Finanzen / Arbeitswelt |
| T16 | Wissenschaft / Technik / Forschung |
| T17 | Politik / Öffentlichkeit / Debatte |
| T18 | Analyse / Interpretation / Argumentation |

`data/taxonomy/themes.yml` MUST define at least:

```yaml
themes:
  - theme_id: "T01"
    slug: "t01"
    title_uk: null
    title_de: null
    description: null
    status: "active"
```

### 25.4. Objectives

Objective IDs use the pattern:

```text
O[0-9]{2}
```

The current corpus includes objective IDs such as:

```text
O01
O02
O03
O04
O05
O06
O07
O08
O09
O10
O11
O12
O15
```

Future objectives require taxonomy change control.

### 25.5. Patterns

Pattern IDs use the pattern:

```text
P[0-9]{2}
```

The current corpus includes pattern IDs such as:

```text
P01
P02
P04
P05
P06
P07
P09
P10
P11
P12
```

Future patterns require taxonomy change control.

### 25.6. Tags

Tags are flexible but controlled.

Rules:

```text
tags are lowercase slugs where possible
tags should not replace primary_theme_id
tags may capture grammar, vocabulary, pragmatic or delivery properties
tags must not contain secrets or personal data
```

### 25.7. Coverage matrix

Coverage is measured by:

```text
cefr_level × primary_theme_id × objective_id × pattern_id
```

This matrix is more important than total item count alone.

---

## 26. Taxonomy Artifact Standard

### 26.1. `cefr_levels.yml`

```yaml
cefr_levels:
  - cefr_level: "A1"
    broad_group: "basic_user"
    order: 1
    status: "active"
  - cefr_level: "A2"
    broad_group: "basic_user"
    order: 2
    status: "active"
  - cefr_level: "B1"
    broad_group: "independent_user"
    order: 3
    status: "active"
  - cefr_level: "B2"
    broad_group: "independent_user"
    order: 4
    status: "active"
  - cefr_level: "C1"
    broad_group: "proficient_user"
    order: 5
    status: "active"
  - cefr_level: "C2"
    broad_group: "proficient_user"
    order: 6
    status: "active"
```

### 26.2. `themes.yml`

```yaml
themes:
  - theme_id: "T01"
    slug: "t01"
    title_uk: null
    title_de: null
    status: "active"
    sort_order: 1
```

### 26.3. `objectives.yml`

```yaml
objectives:
  - objective_id: "O09"
    slug: "o09"
    title_uk: null
    title_de: null
    status: "active"
```

### 26.4. `patterns.yml`

```yaml
patterns:
  - pattern_id: "P01"
    slug: "p01"
    title_uk: null
    title_de: null
    status: "active"
```

### 26.5. `coverage_policy.yml`

```yaml
coverage_policy:
  matrix_dimensions:
    - cefr_level
    - primary_theme_id
    - objective_id
    - pattern_id
  report_zero_cells: true
  include_draft_items: true
  include_approved_items: true
  include_published_items: true
  production_coverage_statuses:
    - approved
    - published
```

---

## 27. Compatibility Standard

### 27.1. API compatibility

An item is `api_delivery_ready=true` when:

```text
status is approved or published
canonical schema validation passed
stem.de exists
options are valid
correct_option_ids are valid
cefr_level is valid
primary_theme_id is valid
source traceability exists
no blocking quality flag exists
```

### 27.2. Telegram compatibility

An item is `telegram_quiz_ready=true` only when Telegram projection can be safely created.

Minimum Telegram validation profile:

```text
question text length: 1–300 characters after projection
options count: 2–12
option text: non-empty and within Telegram adapter limit
quiz mode correct_option_ids: monotonically increasing 0-based integers
explanation: optional, 0–200 characters where used
open_period/close_date: valid when configured
item_type supported by Telegram adapter
```

Telegram rules evolve. The Telegram adapter MUST use a versioned compatibility profile, for example:

```yaml
telegram_compatibility_profiles:
  - profile_id: "tg_poll_quiz_v2026_04"
    bot_api_version: "9.6"
    question_min_chars: 1
    question_max_chars: 300
    options_min: 2
    options_max: 12
    explanation_max_chars: 200
    supports_multiple_correct_answers: true
```

### 27.3. Teacher pack compatibility

Teacher pack compatibility SHOULD require:

```text
approved/published status
valid taxonomy
source traceability
answer key availability
optional explanation or review flag if explanation missing
```

---

## 28. Validation Profile Standard

### 28.1. Validation result object

```json
{
  "validation_result_id": "vr_01J...",
  "subject_type": "quiz_item",
  "subject_id": "qi_01J...",
  "validation_profile_id": "vp_quiz_item_mvp_v1",
  "status": "fail",
  "rule_id": "DS-V-QI-004",
  "severity": "blocker",
  "path": "/options/1/text/de",
  "message": "Option text is empty after normalization.",
  "detected_at": "2026-04-30T18:00:00Z",
  "resolved_at": null,
  "resolved_by": null
}
```

### 28.2. Validation status

```text
pass
warning
fail
```

### 28.3. Validation severity

```text
info
warning
error
blocker
```

### 28.4. Rule severity meaning

| Severity | Meaning |
|---|---|
| `info` | Does not block, useful for reporting. |
| `warning` | Should be reviewed, does not block MVP import unless policy says so. |
| `error` | Blocks approval/publication. |
| `blocker` | Blocks import commit or delivery. |

---

## 29. Validation Rule Catalog

### 29.1. Source validation

| Rule ID | Rule | Severity | Blocks |
|---|---|---|---|
| DS-V-SRC-001 | `source_id` exists and matches pattern. | blocker | registration/import |
| DS-V-SRC-002 | `checksum_sha256` exists before parser assignment. | blocker | parser assignment |
| DS-V-SRC-003 | Source state is valid enum. | blocker | import |
| DS-V-SRC-004 | Importable source has manifest entry. | blocker | dry-run/import |
| DS-V-SRC-005 | Source is not rejected or blocked. | blocker | import/delivery |
| DS-V-SRC-006 | Duplicate source checksum is flagged. | warning/error | activation |

### 29.2. Manifest validation

| Rule ID | Rule | Severity | Blocks |
|---|---|---|---|
| DS-V-MAN-001 | Manifest version exists. | blocker | import |
| DS-V-MAN-002 | Source ID references known source. | blocker | import |
| DS-V-MAN-003 | Parser profile ID references active profile. | blocker | import |
| DS-V-MAN-004 | Defaults use valid CEFR/theme/objective/pattern. | blocker | import |
| DS-V-MAN-005 | Unknown taxonomy values are not silently coerced. | blocker | import |
| DS-V-MAN-006 | Manifest contains no secrets. | blocker | commit |

### 29.3. Parser validation

| Rule ID | Rule | Severity | Blocks |
|---|---|---|---|
| DS-V-PP-001 | Parser profile has ID/version. | blocker | import |
| DS-V-PP-002 | Parser has field mapping. | blocker | import |
| DS-V-PP-003 | Parser has test fixture. | error | production use |
| DS-V-PP-004 | Parser preserves source locator. | blocker | import commit |
| DS-V-PP-005 | Parser emits machine-readable error categories. | error | production use |

### 29.4. Quiz item validation

| Rule ID | Rule | Severity | Blocks |
|---|---|---|---|
| DS-V-QI-001 | `schema_version` exists. | blocker | import/approval |
| DS-V-QI-002 | `quiz_item_id` exists after database import. | blocker | approval |
| DS-V-QI-003 | `stem.de` exists and is non-empty. | blocker | import/approval |
| DS-V-QI-004 | Each option has non-empty `text.de`. | blocker | import/approval |
| DS-V-QI-005 | Options count is at least 2. | blocker | approval/delivery |
| DS-V-QI-006 | `correct_option_ids` is non-empty. | blocker | approval/delivery |
| DS-V-QI-007 | Correct option IDs reference existing options. | blocker | approval/delivery |
| DS-V-QI-008 | `status` is valid enum. | blocker | import/approval |
| DS-V-QI-009 | Approved/published item has CEFR level. | blocker | approval/delivery |
| DS-V-QI-010 | Approved/published item has primary theme. | blocker | approval/delivery |
| DS-V-QI-011 | Approved/published item has objective/pattern. | error/blocker | approval depending on policy |
| DS-V-QI-012 | Item has source traceability. | blocker | approval/delivery |
| DS-V-QI-013 | Item has semantic content hash. | blocker | import/approval |
| DS-V-QI-014 | Item does not contain blocking quality flag. | blocker | delivery |
| DS-V-QI-015 | Single-choice item has exactly one correct option. | blocker | approval/delivery |
| DS-V-QI-016 | Multiple-choice item has at least one correct option. | blocker | approval/delivery |

### 29.5. Taxonomy validation

| Rule ID | Rule | Severity | Blocks |
|---|---|---|---|
| DS-V-TAX-001 | CEFR level is one of A1–C2. | blocker | approval/delivery |
| DS-V-TAX-002 | Theme ID exists in `themes.yml`. | blocker | approval/delivery |
| DS-V-TAX-003 | Objective ID exists in `objectives.yml`. | error | approval |
| DS-V-TAX-004 | Pattern ID exists in `patterns.yml`. | error | approval |
| DS-V-TAX-005 | Tags follow slug policy. | warning | none/review |
| DS-V-TAX-006 | Coverage report can compute level × theme × objective × pattern. | error | demo/pilot |

### 29.6. Status/delivery validation

| Rule ID | Rule | Severity | Blocks |
|---|---|---|---|
| DS-V-STAT-001 | Item has exactly one status. | blocker | all |
| DS-V-STAT-002 | Normal consumers receive only approved/published items. | blocker | delivery |
| DS-V-STAT-003 | Status change has audit record. | error | production claim |
| DS-V-DEL-001 | Delivery record references item version. | error | production claim |
| DS-V-DEL-002 | Delivery record references consumer. | error | production claim |
| DS-V-DEL-003 | Delivery record records status/outcome. | error | production claim |

### 29.7. Telegram validation

| Rule ID | Rule | Severity | Blocks |
|---|---|---|---|
| DS-V-TG-001 | Telegram question text length is valid. | blocker | Telegram delivery |
| DS-V-TG-002 | Telegram options count is 2–12. | blocker | Telegram delivery |
| DS-V-TG-003 | Telegram correct option positions are 0-based and increasing. | blocker | Telegram quiz delivery |
| DS-V-TG-004 | Telegram explanation length is valid where used. | blocker | Telegram delivery |
| DS-V-TG-005 | Item type is supported by Telegram adapter. | blocker | Telegram delivery |
| DS-V-TG-006 | Telegram projection uses canonical item version, not raw file. | blocker | Telegram delivery |

---

## 30. JSON Schema Standard

### 30.1. Schema dialect

Canonical validation SHOULD use JSON Schema Draft 2020-12.

Every schema file SHOULD include:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema"
}
```

### 30.2. Schema file naming

```text
quiz_item.schema.json
normalized_quiz_candidate.schema.json
source_file.schema.json
import_manifest.schema.json
parser_profile.schema.json
delivery.schema.json
attempt.schema.json
entitlement.schema.json
```

### 30.3. Schema design rules

- Use `required` for blocking production fields.
- Use `enum` for status/source state/CEFR values.
- Use `pattern` for stable ID formats where appropriate.
- Use `additionalProperties: false` in strict schema profiles.
- Use `$defs` for reusable enum definitions.
- Schema must validate canonical payloads, not raw CSV rows.
- Raw parser errors should be captured before canonical validation.

---

## 31. Seed `quiz_item.schema.json`

This is a seed schema. Implementation may split it into multiple schemas, but it must preserve the same semantics.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://api-quiz-bank.example/schemas/quiz_item.schema.json",
  "title": "API Quiz Bank Canonical Quiz Item",
  "type": "object",
  "required": [
    "schema_version",
    "quiz_item_id",
    "version_id",
    "status",
    "item_type",
    "language_mode",
    "stem",
    "options",
    "correct_option_ids",
    "taxonomy",
    "source",
    "compatibility",
    "quality",
    "timestamps"
  ],
  "additionalProperties": false,
  "properties": {
    "schema_version": {
      "type": "string",
      "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$"
    },
    "quiz_item_id": {
      "type": "string",
      "pattern": "^qi_[A-Za-z0-9_\\-]+$"
    },
    "version_id": {
      "type": "string",
      "pattern": "^qiv_[A-Za-z0-9_\\-]+$"
    },
    "status": {
      "$ref": "#/$defs/item_status"
    },
    "item_type": {
      "$ref": "#/$defs/item_type"
    },
    "language_mode": {
      "$ref": "#/$defs/language_mode"
    },
    "stem": {
      "$ref": "#/$defs/multilingual_text_required_de"
    },
    "options": {
      "type": "array",
      "minItems": 2,
      "items": {
        "$ref": "#/$defs/quiz_option"
      }
    },
    "correct_option_ids": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "string",
        "pattern": "^qopt_[A-Za-z0-9_\\-]+$"
      }
    },
    "explanation": {
      "$ref": "#/$defs/multilingual_text_optional"
    },
    "taxonomy": {
      "$ref": "#/$defs/taxonomy"
    },
    "source": {
      "$ref": "#/$defs/source_traceability"
    },
    "compatibility": {
      "$ref": "#/$defs/compatibility"
    },
    "quality": {
      "$ref": "#/$defs/quality"
    },
    "timestamps": {
      "$ref": "#/$defs/timestamps"
    },
    "metadata": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "$defs": {
    "item_status": {
      "type": "string",
      "enum": [
        "draft",
        "imported",
        "normalized",
        "needs_review",
        "approved",
        "published",
        "monitored",
        "retired",
        "blocked"
      ]
    },
    "item_type": {
      "type": "string",
      "enum": [
        "single_choice",
        "multiple_choice",
        "gap_fill",
        "matching",
        "ordering",
        "short_answer",
        "cloze",
        "translation_prompt",
        "dialogue_reply"
      ]
    },
    "language_mode": {
      "type": "string",
      "enum": [
        "de_only",
        "de_uk_support",
        "de_en_support",
        "multilingual"
      ]
    },
    "cefr_level": {
      "type": "string",
      "enum": ["A1", "A2", "B1", "B2", "C1", "C2"]
    },
    "multilingual_text_required_de": {
      "type": "object",
      "required": ["de"],
      "additionalProperties": false,
      "properties": {
        "de": {
          "type": "string",
          "minLength": 1
        },
        "uk": {
          "type": ["string", "null"]
        },
        "en": {
          "type": ["string", "null"]
        }
      }
    },
    "multilingual_text_optional": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "de": {
          "type": ["string", "null"]
        },
        "uk": {
          "type": ["string", "null"]
        },
        "en": {
          "type": ["string", "null"]
        }
      }
    },
    "quiz_option": {
      "type": "object",
      "required": ["id", "position", "text", "is_correct"],
      "additionalProperties": false,
      "properties": {
        "id": {
          "type": "string",
          "pattern": "^qopt_[A-Za-z0-9_\\-]+$"
        },
        "position": {
          "type": "integer",
          "minimum": 1
        },
        "text": {
          "$ref": "#/$defs/multilingual_text_required_de"
        },
        "is_correct": {
          "type": "boolean"
        },
        "normalized_text_hash": {
          "type": ["string", "null"],
          "pattern": "^sha256:[a-f0-9]{64}$"
        }
      }
    },
    "taxonomy": {
      "type": "object",
      "required": ["cefr_level", "primary_theme_id", "objective_id", "pattern_id"],
      "additionalProperties": false,
      "properties": {
        "cefr_level": {
          "$ref": "#/$defs/cefr_level"
        },
        "primary_theme_id": {
          "type": "string",
          "pattern": "^T[0-9]{2}$"
        },
        "secondary_theme_ids": {
          "type": "array",
          "items": {
            "type": "string",
            "pattern": "^T[0-9]{2}$"
          },
          "uniqueItems": true
        },
        "objective_id": {
          "type": "string",
          "pattern": "^O[0-9]{2}$"
        },
        "pattern_id": {
          "type": "string",
          "pattern": "^P[0-9]{2}$"
        },
        "tags": {
          "type": "array",
          "items": {
            "type": "string",
            "pattern": "^[a-z0-9][a-z0-9_\\-]*$"
          },
          "uniqueItems": true
        }
      }
    },
    "source_traceability": {
      "type": "object",
      "required": ["source_id", "import_batch_id", "semantic_content_hash"],
      "additionalProperties": false,
      "properties": {
        "source_id": {
          "type": "string",
          "pattern": "^src_[0-9]{6}$"
        },
        "import_batch_id": {
          "type": "string",
          "pattern": "^ib_[A-Za-z0-9_\\-]+$"
        },
        "source_locator": {
          "type": ["object", "null"],
          "additionalProperties": true
        },
        "source_checksum_sha256": {
          "type": ["string", "null"],
          "pattern": "^sha256:[a-f0-9]{64}$"
        },
        "raw_row_hash": {
          "type": ["string", "null"],
          "pattern": "^sha256:[a-f0-9]{64}$"
        },
        "semantic_content_hash": {
          "type": "string",
          "pattern": "^sha256:[a-f0-9]{64}$"
        },
        "canonical_record_hash": {
          "type": ["string", "null"],
          "pattern": "^sha256:[a-f0-9]{64}$"
        }
      }
    },
    "compatibility": {
      "type": "object",
      "required": ["api_delivery_ready", "telegram_quiz_ready", "teacher_pack_ready"],
      "additionalProperties": false,
      "properties": {
        "api_delivery_ready": {
          "type": "boolean"
        },
        "telegram_quiz_ready": {
          "type": "boolean"
        },
        "teacher_pack_ready": {
          "type": "boolean"
        },
        "delivery_block_reason": {
          "type": ["string", "null"]
        }
      }
    },
    "quality": {
      "type": "object",
      "required": ["validation_status", "review_required", "quality_flags"],
      "additionalProperties": false,
      "properties": {
        "validation_status": {
          "type": "string",
          "enum": ["not_checked", "passed", "warning", "failed"]
        },
        "review_required": {
          "type": "boolean"
        },
        "quality_flags": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "duplicate_case_id": {
          "type": ["string", "null"]
        },
        "issue_report_count": {
          "type": "integer",
          "minimum": 0
        },
        "last_reviewed_at": {
          "type": ["string", "null"],
          "format": "date-time"
        }
      }
    },
    "timestamps": {
      "type": "object",
      "required": ["created_at", "updated_at"],
      "additionalProperties": false,
      "properties": {
        "created_at": {
          "type": "string",
          "format": "date-time"
        },
        "updated_at": {
          "type": "string",
          "format": "date-time"
        },
        "imported_at": {
          "type": ["string", "null"],
          "format": "date-time"
        },
        "approved_at": {
          "type": ["string", "null"],
          "format": "date-time"
        },
        "published_at": {
          "type": ["string", "null"],
          "format": "date-time"
        },
        "retired_at": {
          "type": ["string", "null"],
          "format": "date-time"
        },
        "blocked_at": {
          "type": ["string", "null"],
          "format": "date-time"
        }
      }
    }
  }
}
```

### 31.1. Cross-field validations not fully covered by basic JSON Schema

Some constraints require custom validators:

```text
correct_option_ids must reference options[].id
single_choice must have exactly one correct option
approved/published items must have approved_at
published items should have published_at
telegram_quiz_ready requires Telegram compatibility profile pass
api_delivery_ready requires approved/published status unless internal demo override
source_id must exist in source registry
theme/objective/pattern IDs must exist in taxonomy files
semantic_content_hash must match computed normalized content
```

---

## 32. API Projection Standard

### 32.1. Projection principle

API responses are projections of canonical data, not raw database tables and not raw source files.

### 32.2. Public quiz item projection

Normal learner/API delivery response SHOULD include:

```json
{
  "id": "qi_01J...",
  "version_id": "qiv_01J...",
  "stem": {
    "de": "Welche Antwort ist richtig?"
  },
  "options": [
    {
      "id": "qopt_01J_A",
      "position": 1,
      "text": {
        "de": "Option A"
      }
    }
  ],
  "cefr_level": "A2",
  "theme_id": "T09",
  "objective_id": "O09",
  "pattern_id": "P01",
  "item_type": "single_choice"
}
```

### 32.3. Public projection MUST NOT expose by default

```text
raw source path
full source filename if sensitive
checksum values
content hash values
admin notes
validation internals
quality reports
audit logs
correct answer before attempt, unless consumer mode requires answer key
other consumer data
```

### 32.4. Admin projection MAY include

```text
source_id
filename
source_locator
import_batch_id
status
validation errors
duplicate flags
content_hash
status history
audit trail
quality flags
```

### 32.5. Answer key projection

Answer keys are not part of normal public delivery unless the endpoint/consumer is authorized.

Allowed contexts:

```text
admin review
teacher export with entitlement
post-attempt feedback
Telegram quiz payload where platform must send correct_option_ids to Telegram API
```

---

## 33. Telegram Projection Standard

### 33.1. Telegram projection object

```json
{
  "telegram_profile_id": "tg_poll_quiz_v2026_04",
  "chat_id": "@example_channel",
  "question": "Welche Antwort ist richtig?",
  "options": [
    {"text": "Option A"},
    {"text": "Option B"}
  ],
  "type": "quiz",
  "allows_multiple_answers": false,
  "correct_option_ids": [1],
  "explanation": "Kurze Erklärung.",
  "source": {
    "quiz_item_id": "qi_01J...",
    "version_id": "qiv_01J..."
  }
}
```

### 33.2. Position conversion

Canonical option positions are 1-based.

Telegram `correct_option_ids` are 0-based.

Conversion rule:

```text
telegram_position = canonical_position - 1
```

### 33.3. Telegram projection invariants

- Telegram worker MUST NOT read raw CSV.
- Telegram projection MUST be derived from canonical item version.
- Telegram projection MUST pass Telegram compatibility validation before send.
- Telegram delivery MUST create delivery record.
- Telegram errors MUST be recorded with reason code.
- Telegram compatibility profiles MUST be versioned.

---

## 34. Selection Data Standard

### 34.1. Selection input

Selection engine requires:

```text
consumer_id
requested_cefr_levels
requested_theme_ids
requested_objective_ids
requested_pattern_ids
item_type constraints
delivery_channel
repeat_policy
quota context
entitlement context
delivery history
optional deterministic demo seed
```

### 34.2. Selection candidate fields

Quiz candidate selection MUST be able to filter by:

```text
status
cefr_level
primary_theme_id
objective_id
pattern_id
item_type
compatibility flags
quality flags
source state
delivery history
```

### 34.3. Selection output

```json
{
  "selection_request_id": "sel_01J...",
  "consumer_id": "cons_01J...",
  "quiz_item_id": "qi_01J...",
  "version_id": "qiv_01J...",
  "reason": "eligible_by_level_theme_status_quota",
  "filters_applied": [
    "status",
    "cefr_level",
    "theme",
    "repeat_policy",
    "entitlement"
  ],
  "selected_at": "2026-04-30T18:00:00Z"
}
```

### 34.4. No eligible item output

The data layer must support machine-readable no-candidate reason:

```text
no_items_for_level
no_items_for_theme
all_candidates_recently_delivered
quota_exceeded
entitlement_missing
consumer_inactive
status_filter_excluded_all
telegram_compatibility_excluded_all
```

---

## 35. Delivery Data Standard

### 35.1. Delivery fields

```text
delivery_id
consumer_id
quiz_item_id
quiz_item_version_id
selection_request_id
delivery_channel
delivery_status
delivery_reason_code
delivered_at
reserved_at
failed_at
telegram_message_id
api_request_id
idempotency_key
payload_hash
```

### 35.2. Delivery statuses

```text
reserved
sent
delivered
failed
skipped
cancelled
expired
denied
```

### 35.3. Delivery invariants

- Delivery MUST reference item version, not just item.
- Delivery MUST reference consumer.
- Delivery MUST preserve enough payload snapshot or payload hash to explain what was sent.
- Failed delivery SHOULD still be recorded.
- Delivery records MUST NOT be deleted when item is retired.
- Repeat policy must use delivery history.

---

## 36. Attempt Data Standard

### 36.1. Attempt fields

```text
attempt_id
delivery_id
consumer_id
user_id_or_external_user_ref
quiz_item_id
quiz_item_version_id
selected_option_ids
is_correct
response_time_ms
submitted_at
attempt_source
idempotency_key
metadata
```

### 36.2. Attempt privacy

For MVP, attempt data SHOULD minimize personal data.

Allowed without expanded privacy/legal model:

```text
anonymous attempt count
consumer-level aggregate attempt
pseudonymous user reference
selected option IDs
correctness
timestamp
response time
```

Avoid storing:

```text
unnecessary names
phone numbers
private chat content
unneeded Telegram user profile data
```

### 36.3. Attempt invariants

- Attempt should reference delivery where possible.
- Attempt selected options must reference the item version delivered.
- Retired items may still accept attempts for historical delivery if policy allows.
- Attempt analytics must not expose another consumer’s data.

---

## 37. Consumer, Entitlement and Quota Data Standard

### 37.1. Consumer fields

```text
consumer_id
consumer_type
owner_id
name
status
created_at
updated_at
default_cefr_levels
default_theme_ids
delivery_channels
metadata
```

Allowed `consumer_type`:

```text
api_client
telegram_channel
telegram_bot
web_app
school_account
teacher_account
internal_demo
```

Allowed `consumer.status`:

```text
active
inactive
suspended
demo
archived
blocked
```

### 37.2. Consumer rule fields

```text
consumer_rule_id
consumer_id
allowed_cefr_levels
allowed_theme_ids
allowed_objective_ids
allowed_pattern_ids
allowed_item_types
daily_limit
monthly_limit
repeat_policy_id
schedule_id
is_active
created_at
updated_at
```

### 37.3. Entitlement fields

```text
entitlement_id
scope_type
scope_id
feature_code
allowed_values
quota_limit
quota_period
status
valid_from
valid_until
created_by
reason
```

Allowed `scope_type`:

```text
consumer
user
school
organization
api_client
manual_demo
```

Allowed entitlement statuses:

```text
active
inactive
expired
revoked
suspended
manual_override
```

### 37.4. Quota usage fields

```text
quota_usage_id
scope_type
scope_id
feature_code
period_start
period_end
used_count
limit_count
last_incremented_at
```

### 37.5. Access rule

Payment provider state is not access truth.

Access truth:

```text
internal entitlement + quota + consumer status + rule compatibility
```

---

## 38. Analytics and Reporting Data Standard

### 38.1. Required MVP reports

```text
inventory report
source onboarding report
import report
validation report
coverage report
status distribution report
delivery report
quota/entitlement report
demo evidence report
```

### 38.2. Coverage report fields

```text
cefr_level
primary_theme_id
objective_id
pattern_id
item_count_total
item_count_draft
item_count_approved
item_count_published
item_count_retired
item_count_blocked
coverage_status
last_generated_at
```

### 38.3. Import report fields

```text
source_id
import_batch_id
parser_profile_id
source_checksum_sha256
rows_seen
rows_parsed
candidates_created
schema_valid
schema_invalid
duplicates
conflicts
items_created
items_updated
recommendation
report_generated_at
```

### 38.4. Delivery report fields

```text
consumer_id
delivery_channel
delivered_count
failed_count
skipped_count
denied_count
repeat_policy_blocks
quota_blocks
period_start
period_end
```

### 38.5. Analytics integrity

Analytics must be derived from system records, not manually invented numbers.

Reports should distinguish:

```text
all items
draft items
approved items
published items
delivery-eligible items
Telegram-compatible items
API-compatible items
```

---

## 39. Duplicate and Conflict Data Standard

### 39.1. Duplicate classifications

```text
exact_duplicate
near_duplicate
answer_conflict
metadata_conflict
source_duplicate
acceptable_variant
supersession_candidate
```

### 39.2. Duplicate case fields

```text
duplicate_case_id
case_type
severity
status
detection_method
similarity_score
primary_item_id
primary_candidate_id
created_from_import_batch_id
created_at
resolved_at
resolved_by
resolution_decision
resolution_note
```

### 39.3. Resolution decisions

```text
keep_existing
import_as_new_version
import_as_variant
merge_metadata
reject_candidate
block_candidate
retire_existing_and_replace
requires_human_review
```

### 39.4. Duplicate invariants

- Exact duplicates SHOULD NOT become multiple active published items.
- Answer conflicts MUST NOT be auto-published.
- Near duplicates MAY be accepted only with documented resolution.
- Duplicate resolution MUST be auditable.

---

## 40. Quality Flags Standard

### 40.1. Quality flag examples

```text
missing_explanation
telegram_incompatible
duplicate_candidate
answer_conflict
taxonomy_low_confidence
reported_wrong_answer
needs_teacher_review
source_blocked
parser_warning
metadata_incomplete
```

### 40.2. Blocking flags

The following flags SHOULD block normal delivery:

```text
answer_conflict
reported_wrong_answer_high_severity
source_blocked
schema_invalid
correct_answer_unresolved
blocked_by_admin
```

### 40.3. Non-blocking flags

The following flags MAY allow delivery depending on policy:

```text
missing_explanation
taxonomy_low_confidence
minor_parser_warning
teacher_review_recommended
```

For paid/public production, non-blocking warnings should still be visible in admin reports.

---

## 41. Data Exposure and Privacy Standard

### 41.1. Data exposure principle

Expose the minimum data needed for the consumer context.

### 41.2. Public/learner projection

MAY expose:

```text
quiz item ID
stem
options
level
theme
allowed metadata
post-attempt result if applicable
```

MUST NOT expose by default:

```text
source path
internal checksums
admin notes
other consumer data
answer key before attempt
billing internals
audit logs
```

### 41.3. Admin projection

MAY expose:

```text
source traceability
status
validation errors
duplicate/conflict information
quality flags
audit history
```

### 41.4. Analytics projection

Default analytics SHOULD be aggregate.

Detailed user/consumer-level analytics require authorization.

### 41.5. Secrets

No data artifact may contain:

```text
API keys
bot tokens
payment provider secrets
database passwords
private personal data not needed for the artifact
```

---

## 42. Database Mapping Standard

This document is not a final SQL schema, but canonical data must be mappable to relational storage.

### 42.1. Core tables

```text
source_files
parser_profiles
import_manifest_entries
import_batches
normalized_quiz_candidates
validation_results
duplicate_cases
quiz_items
quiz_item_versions
quiz_options
quiz_item_status_events
taxonomy_themes
taxonomy_objectives
taxonomy_patterns
taxonomy_tags
quiz_item_tags
consumers
consumer_rules
entitlements
quota_usage
deliveries
attempts
attempt_answers
audit_logs
generated_reports
```

### 42.2. Minimum constraints

```text
source_files.source_id unique
source_files.checksum_sha256 indexed
quiz_items.public_id unique
quiz_items.content_hash indexed
quiz_items.status indexed
quiz_items.cefr_level indexed
quiz_items.primary_theme_id indexed
quiz_options.quiz_item_version_id foreign key
deliveries.consumer_id indexed
deliveries.quiz_item_id indexed
deliveries.quiz_item_version_id indexed
entitlements scope fields indexed
audit_logs resource fields indexed
```

### 42.3. Query requirements

Database design must support:

```text
selection by status + level + theme + objective + pattern
source traceability lookup by quiz_item_id
delivery history lookup by consumer and item
coverage matrix generation
duplicate detection by semantic_content_hash
admin review filtering by source/status/validation
quota checks by consumer/period/feature
```

---

## 43. Schema Evolution and Migration Standard

### 43.1. Schema change categories

| Change | Example | Required action |
|---|---|---|
| Add optional field | Add `difficulty_seed` | Schema minor version, docs update |
| Add required field | Require `objective_id` | Major version or migration gate |
| Rename field | `theme_id` to `primary_theme_id` | Major version + migration |
| Change enum | Add `experimental` status | Data standard update + tests |
| Change hash algorithm | `semantic_content_hash_v2` | New field or version marker |
| Tighten validation | Reject previously valid items | Migration plan + impact report |

### 43.2. Migration evidence

Data migrations SHOULD produce:

```text
migration_id
before_count
after_count
affected_entities
validation_before
validation_after
rollback_plan
owner
timestamp
```

### 43.3. Backward compatibility

The system MAY support multiple schema versions during migration, but production delivery should use the current approved schema version or documented compatibility bridge.

---

## 44. Future Source Onboarding Data Playbook

### 44.1. New file intake

```text
1. Receive file in controlled intake location.
2. Create source_intake record.
3. Assign source_id.
4. Compute source_checksum_sha256.
5. Add file_inventory record.
6. Add import_manifest entry.
7. Assign parser_profile.
8. Run dry-run import.
9. Generate import report.
10. Validate normalized candidates.
11. Classify duplicates/conflicts.
12. Import valid candidates into canonical storage.
13. Assign statuses.
14. Approve/publish eligible items.
15. Regenerate coverage/inventory reports.
16. Record changelog/release note if production corpus changed.
```

### 44.2. Onboarding acceptance criteria

A new source is accepted only when:

```text
source_id exists
checksum exists
inventory record exists
manifest entry exists
parser profile assigned
dry-run report exists
schema validation completed
duplicate/conflict results classified
items have source traceability
approved items meet canonical requirements
coverage report updated
```

### 44.3. Onboarding rejection criteria

Reject or block candidate source when:

```text
file format cannot be parsed
checksum duplicates an active source without justification
rights_status is unknown/rejected for production use
correct answers cannot be resolved
systemic schema failures exist
taxonomy cannot be mapped
source violates storage/security policy
admin/product owner rejects it
```

---

## 45. Generated Reports Standard

### 45.1. Generated report metadata

Every generated report SHOULD include:

```text
report_id
report_type
generated_by
generated_at
input_paths_or_source_ids
input_checksums
tool_version
summary
limitations
```

### 45.2. Generated report types

```text
inventory_report
coverage_report
constitution_check_report
schema_validation_report
import_report
duplicate_report
delivery_report
quota_report
demo_evidence_report
```

### 45.3. Report consistency rule

Generated README/inventory snapshots should not be manually edited unless explicitly marked as manual.

If report and source data disagree, source data + generation tool must be inspected.

---

## 46. Data Test Standard

### 46.1. Test categories

```text
schema validation tests
parser fixture tests
manifest validation tests
source inventory tests
checksum tests
content hash tests
taxonomy enum tests
status delivery gate tests
Telegram compatibility tests
API projection tests
duplicate detection tests
coverage report tests
entitlement/quota data tests
migration tests
demo fixture tests
```

### 46.2. P0 data tests

Before MVP acceptance:

```text
current corpus inventory can be generated or inspected
new sample source can be registered
checksum can be computed
manifest can be validated
parser can dry-run at least one source
canonical schema validates sample item
draft item is blocked from normal delivery
approved item passes API projection validation
Telegram-compatible item passes Telegram profile validation
coverage report can be generated
```

### 46.3. Validation command examples

```bash
python3 tools/quizbank_inventory.py --quizbank-dir QuizBank --format json
python3 tools/quizbank_constitution_check.py --quizbank-dir QuizBank --format json
python3 tools/validate_manifest.py --manifest data/manifests/import_manifest.yml
python3 tools/validate_schema.py --schema data/schemas/quiz_item.schema.json --input data/normalized/quiz_items.sample.jsonl
python3 tools/run_import.py --source-id src_000001 --dry-run
python3 tools/coverage_report.py --format json
```

Tool names are illustrative unless already implemented.

---

## 47. Launch Gates — Data

### 47.1. MVP data gate

MVP data gate passes when:

```text
DG-MVP-001  Source inventory exists or generation workflow exists.
DG-MVP-002  Import manifest exists for at least one pilot source.
DG-MVP-003  Parser profile exists for at least one pilot source.
DG-MVP-004  Dry-run import produces structured report.
DG-MVP-005  Canonical quiz item schema exists.
DG-MVP-006  At least one canonical item sample validates.
DG-MVP-007  Status enum is enforced.
DG-MVP-008  Draft items cannot be selected for normal delivery.
DG-MVP-009  Approved/published items require source traceability.
DG-MVP-010  Coverage report can be produced.
DG-MVP-011  Future source onboarding can be demonstrated on a sample file or artifact.
```

### 47.2. Pilot data gate

Pilot data gate passes when:

```text
DG-PILOT-001  All pilot sources have source_id/checksum/manifest entries.
DG-PILOT-002  Pilot import is reproducible from source checksum + manifest + parser version.
DG-PILOT-003  Duplicate/conflict report exists.
DG-PILOT-004  API projection tests pass.
DG-PILOT-005  Telegram compatibility tests pass for Telegram pilot.
DG-PILOT-006  Delivery records reference item versions.
DG-PILOT-007  Entitlement/quota data model is operational for pilot consumers.
DG-PILOT-008  Generated reports distinguish draft/approved/published items.
```

### 47.3. Production data gate

Production data gate passes when:

```text
DG-PROD-001  Production corpus is imported through controlled pipeline.
DG-PROD-002  No normal consumer can access raw CSV.
DG-PROD-003  Schema validation is automated in CI or release workflow.
DG-PROD-004  Status and compatibility gates are tested.
DG-PROD-005  Source traceability is queryable for every deliverable item.
DG-PROD-006  Delivery logs and repeat policy data are reliable.
DG-PROD-007  Backup/restore covers production data.
DG-PROD-008  Data-impacting changes require PR/change control.
DG-PROD-009  Known data limitations are documented.
```

---

## 48. Stanford-Ready Data Demo

### 48.1. Demo must show

```text
current corpus baseline
file inventory
source_id and checksum for a source
import_manifest.yml entry
parser_profile
dry-run import report
canonical quiz item schema
validated canonical item sample
status rule: draft is blocked
approved item projection
Telegram compatibility profile or dry-run payload
delivery log
coverage report
future source onboarding path
```

### 48.2. Demo must not claim

```text
that CSV files are production product
that all draft items are public-ready
that future file drops are accepted without onboarding
that Telegram bot owns selection logic
that billing provider state alone controls access
that planned fields are implemented if they are only documented
```

### 48.3. Demo evidence files

Recommended:

```text
reports/demo/demo_inventory_snapshot.md
reports/demo/demo_source_onboarding.md
reports/demo/demo_import_report.json
reports/demo/demo_validation_result.json
reports/demo/demo_canonical_item.json
reports/demo/demo_api_response.json
reports/demo/demo_telegram_payload.json
reports/demo/demo_delivery_log.json
reports/demo/demo_coverage_report.json
```

---

## 49. Traceability Matrix

| Data standard area | SRS areas | Use cases | Domain entities |
|---|---|---|---|
| Source inventory | SRC, ONB, DOC | UC-001, UC-030 | `source_file`, `source_inventory_record` |
| Import manifest | IMP, ONB | UC-002, UC-016 | `import_manifest_entry`, `parser_profile` |
| Dry-run/import report | IMP, QA, DOC | UC-002, UC-017 | `import_batch`, `import_report` |
| Normalized candidate | IMP, DATA | UC-002, UC-003 | `normalized_quiz_candidate` |
| Canonical quiz item | DATA, DB | UC-004, UC-005 | `quiz_item`, `quiz_item_version`, `quiz_option` |
| Taxonomy | TAX | UC-009, UC-012 | `taxonomy_theme`, `taxonomy_objective`, `taxonomy_pattern` |
| Status lifecycle | STAT | UC-004, UC-011, UC-019 | `quiz_item_status_event` |
| API projection | API, SEL, CONS | UC-005, UC-027 | `selection_request`, `delivery` |
| Telegram projection | TG, SEL | UC-007, UC-022 | `telegram_delivery_payload`, `delivery` |
| Entitlement/quota data | BILL, CONS | UC-008, UC-013, UC-023 | `entitlement`, `quota_usage` |
| Delivery/attempt data | AN, DB | UC-006, UC-007, UC-029 | `delivery`, `attempt`, `attempt_answer` |
| Analytics reports | AN, DOC, DEMO | UC-012, UC-015, UC-029 | `analytics_report`, `generated_report` |
| Future source onboarding | ONB, IMP, QA | UC-001, UC-030 | `source_onboarding_run`, `source_file` |

---

## 50. Open Data Questions

These questions should be resolved in implementation planning, `07_api_standard.md`, `09_quality_assurance.md`, or database migration design.

```text
OQ-DS-001  Should public item IDs be ULID-based, UUID-based or generated custom IDs?
OQ-DS-002  Should semantic_content_hash preserve option order or canonicalize option order for dedupe?
OQ-DS-003  Should taxonomy fields be included in canonical_record_hash v1?
OQ-DS-004  Should approved and published remain separate statuses in MVP?
OQ-DS-005  Should item version snapshots store full payload or normalized content columns only?
OQ-DS-006  What exact first parser profiles are needed for current CSV variations?
OQ-DS-007  Which future source formats are first-class after CSV: XLSX, JSONL, Google Sheets export?
OQ-DS-008  Which item types beyond single_choice/multiple_choice are first supported?
OQ-DS-009  How much Telegram payload snapshot should delivery store?
OQ-DS-010  Should coverage cells be materialized or generated only?
OQ-DS-011  What exact retention policy applies to attempts?
OQ-DS-012  What exact admin workflow stores review decisions in MVP?
OQ-DS-013  Which OpenAPI version will be locked in 07_api_standard.md?
OQ-DS-014  How should AI-assisted metadata suggestions be marked if added later?
OQ-DS-015  What minimum data should be included in teacher exports?
```

---

## 51. Reference Standards and Alignment

This Data Standard aligns with:

```text
Stanford/SLAC-style requirements discipline:
- goal → requirements → use cases → tests → traceability → change control

CEFR:
- A1, A2, B1, B2, C1, C2 canonical level values

JSON Schema Draft 2020-12:
- canonical data validation and machine-checkable schema files

OpenAPI Specification:
- API projections and schema components in docs/07_api_standard.md

RFC 9457 Problem Details:
- machine-readable API/import/validation error model alignment

Telegram Bot API:
- Telegram quiz/poll delivery compatibility validation

OWASP API Security:
- object-level authorization, object-property authorization and safe data exposure

PostgreSQL / relational database discipline:
- constraints, indexes, versioned migrations and referential integrity

Git/GitHub discipline:
- versioned data artifacts, PR review, CI validation and generated reports
```

Reference URLs:

```text
Stanford/SLAC Requirements Methodology:
https://www-group.slac.stanford.edu/cdsoft/nlc_arch/nlc_requirements/RequirementsMethod.pdf

CEFR level descriptions:
https://www.coe.int/en/web/common-european-framework-reference-languages/level-descriptions

JSON Schema Draft 2020-12:
https://json-schema.org/draft/2020-12

OpenAPI Specification latest:
https://spec.openapis.org/oas/latest.html

OpenAPI Specification 3.2.0:
https://spec.openapis.org/oas/v3.2.0.html

RFC 9457 Problem Details:
https://www.rfc-editor.org/rfc/rfc9457.html

Telegram Bot API:
https://core.telegram.org/bots/api

OWASP API Security:
https://owasp.org/API-Security/
```

---

## 52. Acceptance Criteria for This Data Standard

This document is accepted when it satisfies:

```text
DS-AC-001  It defines canonical data artifacts and their authority.
DS-AC-002  It supports current corpus baseline.
DS-AC-003  It supports future source onboarding.
DS-AC-004  It defines file inventory and import manifest rules.
DS-AC-005  It defines parser profile requirements.
DS-AC-006  It defines normalized candidate requirements.
DS-AC-007  It defines canonical quiz item fields.
DS-AC-008  It defines option/correct-answer representation.
DS-AC-009  It defines CEFR/theme/objective/pattern taxonomy rules.
DS-AC-010  It defines item statuses and delivery eligibility.
DS-AC-011  It defines source states.
DS-AC-012  It defines checksum and content hash policy.
DS-AC-013  It defines validation rule catalog.
DS-AC-014  It includes seed JSON Schema for canonical item.
DS-AC-015  It defines API and Telegram projection rules.
DS-AC-016  It defines delivery, attempt, entitlement and analytics data basics.
DS-AC-017  It defines generated reports.
DS-AC-018  It defines data launch gates.
DS-AC-019  It defines Stanford-ready data demo evidence.
DS-AC-020  It is ready to inform `data/schemas/*.schema.json`, `data/manifests/*.yml`, database migrations, validators and API schemas.
```

---

## 53. Final Data Standard Rule

The final rule:

```text
A quiz item is not a product item because it appears in a file.

A quiz item becomes product data only when it has:
stable identity,
source traceability,
canonical schema,
valid answer references,
CEFR/theme/objective/pattern taxonomy,
status,
version,
content hash,
validation result,
consumer compatibility,
and a controlled path to delivery, analytics and audit.
```

Therefore:

```text
No canonical data, no API product.
No source traceability, no trust.
No validation, no scale.
No status gate, no delivery.
No onboarding path, no future growth.
```
